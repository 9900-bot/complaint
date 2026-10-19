"""Report example-pair scores; small diagnostic, not a benchmark or calibration."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.ml import ModelRuntime
from app.config import settings

PAIRS=[
    ('near duplicate','The streetlights on our road are broken.','The street lights on our road are not working.'),
    ('paraphrase','There is no drinking water supply to our homes.','Our taps have been dry for three days.'),
    ('unrelated','The streetlights on our road are broken.','The local bus service is frequently delayed.'),
    ('ambiguous','The street floods after rain and the lights stop working.','The drainage channel is blocked.'),
]
runtime=ModelRuntime()
runtime.load(download=True)
results=[]
for kind,a,b in PAIRS:
    cosine=float(runtime.embed(a)@runtime.embed(b))
    cross=float(runtime.score([(a,b)])[0])
    results.append({'example':kind,'cosine':round(cosine,5),'assignment_pass':cosine>=settings.membership_threshold,
                    'cross_similarity':round(cross,5),'merge_pass':cross>settings.merge_threshold})
output={'membership_threshold':settings.membership_threshold,'merge_threshold':settings.merge_threshold,
        'warning':'Small English diagnostic set, not calibrated probability or a representative accuracy benchmark.','pairs':results}
print(json.dumps(output,indent=2))
target=Path(__file__).resolve().parents[1]/'outputs/model-evaluation.json'
target.parent.mkdir(exist_ok=True)
target.write_text(json.dumps(output,indent=2))
