from itertools import combinations
import numpy as np
from sqlalchemy import select, update
from app.models import Cluster, Complaint, ClusterMerge, now
from app.ml import SQLiteVectors, exact_nearest, normalize
from app.labels import LabelService
from app.config import settings


class ClusterService:
    def __init__(self, runtime, config=settings, vectors=None, labels=None):
        self.runtime = runtime
        self.config = config
        self.vectors = vectors or SQLiteVectors()
        self.labels = labels or LabelService()

    def members(self, db, cluster_id):
        return list(db.scalars(select(Complaint).where(Complaint.cluster_id == cluster_id).order_by(Complaint.created_at, Complaint.id)))

    def refresh(self, db, cluster):
        db.flush()
        members = self.members(db, cluster.id)
        matrix = np.stack([self.vectors.deserialize(m.embedding, m.embedding_dimension) for m in members])
        centroid = normalize(matrix.mean(axis=0))
        representative = members[int(np.argmax(matrix @ centroid))]
        cluster.centroid_embedding = self.vectors.serialize(centroid)
        cluster.complaint_count = len(members)
        cluster.representative_text = representative.original_text
        cluster.label = self.labels.label([m.original_text for m in members])
        cluster.updated_at = now()
        db.flush()

    def assign(self, db, complaint, embedding):
        if complaint.cluster_id:
            return db.get(Cluster, complaint.cluster_id)
        embedding = normalize(embedding)
        active = list(db.scalars(select(Cluster).where(Cluster.active).order_by(Cluster.created_at, Cluster.id)))
        if any(c.embedding_model_version != self.runtime.version or c.embedding_dimension != embedding.size for c in active):
            raise ValueError('Embedding model changed; explicit re-embedding is required')
        nearest, similarity = exact_nearest(embedding, active, self.vectors)
        if nearest is None or similarity < self.config.membership_threshold:
            nearest = Cluster(label=self.labels.label([complaint.original_text]), representative_text=complaint.original_text,
                              centroid_embedding=self.vectors.serialize(embedding), embedding_dimension=embedding.size,
                              embedding_model_version=self.runtime.version, complaint_count=0)
            db.add(nearest)
            db.flush()
        complaint.embedding = self.vectors.serialize(embedding)
        complaint.embedding_dimension = embedding.size
        complaint.embedding_model_version = self.runtime.version
        complaint.cluster_id = nearest.id
        self.refresh(db, nearest)
        return nearest

    def candidates(self, db):
        active = list(db.scalars(select(Cluster).where(Cluster.active).order_by(Cluster.created_at, Cluster.id)))
        if len(active) < 2:
            return []
        matrix = np.stack([self.vectors.deserialize(c.centroid_embedding, c.embedding_dimension) for c in active])
        scores = matrix @ matrix.T
        pairs = [(float(scores[i, j]), active[i], active[j]) for i, j in combinations(range(len(active)), 2)
                 if scores[i, j] >= self.config.merge_candidate_similarity]
        return sorted(pairs, key=lambda p: (-p[0], p[1].id, p[2].id))[:self.config.merge_top_k]

    def merge(self, db, first_id, second_id, score):
        first, second = db.get(Cluster, first_id), db.get(Cluster, second_id)
        if not first or not second or first.id == second.id or not first.active or not second.active:
            return None
        if score <= self.config.merge_threshold:
            return None
        target, source = sorted([first, second], key=lambda c: (c.created_at, c.id))
        db.execute(update(Complaint).where(Complaint.cluster_id == source.id).values(cluster_id=target.id))
        source.active = False
        source.complaint_count = 0
        source.updated_at = now()
        db.add(ClusterMerge(source_cluster_id=source.id, target_cluster_id=target.id, merge_score=score,
                            model_version=self.runtime.cross_version))
        self.refresh(db, target)
        return target

    def merge_candidates(self, db):
        for _ in range(self.config.merge_iterations):
            merged = False
            for _, a, b in self.candidates(db):
                pairs = [(a.representative_text, b.representative_text)]
                members_a, members_b = self.members(db, a.id), self.members(db, b.id)
                if len(members_a) > 1 or len(members_b) > 1:
                    ma = np.stack([self.vectors.deserialize(m.embedding, m.embedding_dimension) for m in members_a])
                    mb = np.stack([self.vectors.deserialize(m.embedding, m.embedding_dimension) for m in members_b])
                    ia, ib = np.unravel_index(int(np.argmin(ma @ mb.T)), (len(ma), len(mb)))
                    pairs.append((members_a[ia].original_text, members_b[ib].original_text))
                score = float(min(self.runtime.score(pairs)))
                if score > self.config.merge_threshold:
                    self.merge(db, a.id, b.id, score)
                    merged = True
                    break  # Re-evaluate after each merge; never merge connected components blindly.
            if not merged:
                break

    def process(self, db, complaint, embedding):
        self.assign(db, complaint, embedding)
        self.merge_candidates(db)
        complaint.internal_processing_state = 'completed'
