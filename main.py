from flask import Flask, render_template, request
import os
import typing
import json
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient


app = Flask(__name__)

endpoint = os.getenv('endpoint')
key = os.getenv('key')


text_analytics_client = TextAnalyticsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)

@app.route('/', methods=['GET', 'POST'])
def index():
    documents = []
    text=[]
    reviews=[]
    sentences=[]
    if request.method == 'POST':
        # Check if the POST request has a file part
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        # If the user does not select a file, the browser submits an empty file without a filename
        if file.filename == '':
            return 'No selected file'
        # Save the uploaded file
        filename = os.path.join('uploads', file.filename)
        file.save(filename)
        f = open(filename)
        data = json.load(f)
        for i in data['reviews']:
            documents.append(i["content"])
        f.close()

        result = text_analytics_client.analyze_sentiment(documents, show_opinion_mining=True)
        doc_result = [doc for doc in result if not doc.is_error]
  
        text.append("\nبررسی انجام شد")
        positive_reviews = [doc for doc in doc_result if doc.sentiment == "positive"]
        mixed_reviews = [doc for doc in doc_result if doc.sentiment == "mixed"]
        negative_reviews = [doc for doc in doc_result if doc.sentiment == "negative"]
        text.append("...شرح نتایج \n {} نظر مثبت,\n {} نظر مختلط,\n  {} نظر منفی ".format(
            len(positive_reviews), len(mixed_reviews), len(negative_reviews)
        ))
        reviews=[ len(positive_reviews), len(mixed_reviews), len(negative_reviews)]
        text.append("\nاز آنجایی که نظرات این‌گونه مختلط به نظر می‌رسند و به دلیل علاقه‌ی من به دقیق‌ترین یافتن نقاط قابل بهبود کسب و کارم،بیایید نقدهایی که کاربران درباره‌ی جنبه‌های خاصی از کسب و کار دارند را پیدا کنیم")
        text.append("\nرای انجام این کار، من قصد دارم نظرات که دارای احساس منفی هستند را استخراج کنم")
        
        target_to_complaints: typing.Dict[str, typing.Any] = {}
     
        for document in doc_result:
            # sentences=document.sentences
            for sentence in document.sentences:
                sentences.append([sentence.text,sentence.confidence_scores,sentence.sentiment])
                if sentence.mined_opinions:
                    for mined_opinion in sentence.mined_opinions:
                        target = mined_opinion.target
                        if target.sentiment == 'negative':
                            target_to_complaints.setdefault(target.text, [])
                            target_to_complaints[target.text].append(mined_opinion)


        for target_name, complaints in target_to_complaints.items():
            text.append("کاربران {}  نارضایتی درباره '{}'  , مخصوصا گفتند که '{}' است".format(
                len(complaints),
                target_name,
                "', '".join(
                    [assessment.text for complaint in complaints for assessment in complaint.assessments]
                )
            )
            )


        # return f'File uploaded successfully: {filename}'

    return render_template('index.html',text=text,reviews=reviews,results=sentences)

if __name__ == '__main__':
    app.run(debug=True)
