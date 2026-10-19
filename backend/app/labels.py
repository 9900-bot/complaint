import re
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS


class LabelService:
    def label(self, texts):
        try:
            extractor = TfidfVectorizer(ngram_range=(1, 3), max_features=6000,
                                        token_pattern=r'(?u)\b[^\W\d_][^\W\d_]+\b')
            values = extractor.fit_transform(texts)
            names = extractor.get_feature_names_out()
            weights = values.mean(axis=0).A1
            # Prefer informative phrases without imposing a predefined taxonomy.
            # Keep words adjacent in the original text; prefer an actual short phrase.
            phrases = [(i, name) for i, name in enumerate(names) if len(name.split()) >= 2 and
                       all(word not in ENGLISH_STOP_WORDS for word in name.split()) and
                       any(re.search(r'\b' + r'\s+'.join(map(re.escape,name.split())) + r'\b', text.lower()) for text in texts)]
            if not phrases:
                phrases = [(i,name) for i,name in enumerate(names) if name not in ENGLISH_STOP_WORDS]
            scores = [(weights[i] * (1 + .15 * (len(name.split()) - 2)), name) for i,name in phrases]
            return max(scores, key=lambda x: (x[0], x[1]))[1].title()[:90]
        except ValueError:
            words = re.findall(r'\w+', texts[0], flags=re.UNICODE)
            return ' '.join(words[:5])[:90] or 'Reported concern'
