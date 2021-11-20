import fasttext
import pyonmttok


def preprocess(text):
    text = str(text).strip().replace("\n", " ").replace("\xa0", " ").lower()
    tokens, _ = tokenizer.tokenize(text)
    text = " ".join(tokens)
    return text


if __name__ == "__main__":
    line = "Украина Россия"
    tokenizer = pyonmttok.Tokenizer("conservative", joiner_annotate=False)
    model = fasttext.load_model("ru_cat.ftz")
    words = line.strip().split(" ")
    text = " ".join(words[1:])
    predicted_label = model.predict([text])[0][0][0][9:]
    print("P: {} | {}".format(predicted_label, text))
