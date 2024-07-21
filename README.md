# Sentiment Analysis

Main motive of this repo is to provide scoring based on the sentiments using ML models like **Logistic Regression, Support Vector Machine and Naive Bayes**

## Installation of packages

Packages to be installed are added in requirements.txt file, you can install it using following cmd in cmd terminal

```bash
pip install -r requirements.txt
```

## Load the dataset

Load the dataset containing manual labelling of paragraphs named "Dataset.csv" , the dataset should contain more that 2k datas for proper accuracy and precision.

It will futher group data based on the labels and provide indexes for such.

## Data Preprocessing

Data provided in csv file are futher preprocessed using **NLTK** firstly by converting those data to **lower case** , then remove **strip whitespace, and remove newline characters**, futher **Remove non-alphabetic characters and non-ASCII characters, Remove URLs**

After removing above, extracted text are **tokenized** using **RegexpTokenizer.**

Thereafter stopwords are listed in array to be removed from the tokenized text.

Filter out the short words, firstly extracting shorter words with length less than 2 words, then joining it with "string".

Lemmatize text (Text normalization) : It converts the extracted text to its base form of words using **lemmatize.**

## Visualization

Using 2 libraries for visualization :

* `seaborn` is a statistical data visualization library.
* `matplotlib.pyplot` is a plotting library used for creating static, interactive, and animated visualizations.
