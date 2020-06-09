from flask import Flask,render_template,url_for,request,flash
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import PorterStemmer
import math

app=Flask(__name__)
app.secret_key = 'asrtarstaursdlarsn'


def _create_frequency_matrix(sentences):
    frequency_matrix = {}
    stopWords = set(stopwords.words("english"))
    ps = PorterStemmer()

    for sent in sentences:
        freq_table = {}
        words = word_tokenize(sent)
        for word in words:
            word = word.lower()
            word = ps.stem(word)
            if word in stopWords:
                continue

            if word in freq_table:
                freq_table[word] += 1
            else:
                freq_table[word] = 1

        frequency_matrix[sent[:15]] = freq_table

    return frequency_matrix

def _create_tf_matrix(freq_matrix):
    tf_matrix = {}

    for sent, f_table in freq_matrix.items():
        tf_table = {}

        count_words_in_sentence = len(f_table)
        for word, count in f_table.items():
            tf_table[word] = count / count_words_in_sentence

        tf_matrix[sent] = tf_table

    return tf_matrix


def _create_documents_per_words(freq_matrix):
    word_per_doc_table = {}

    for sent, f_table in freq_matrix.items():
        for word, count in f_table.items():
            if word in word_per_doc_table:
                word_per_doc_table[word] += 1
            else:
                word_per_doc_table[word] = 1

    return word_per_doc_table


def _create_idf_matrix(freq_matrix, count_doc_per_words, total_documents):
    idf_matrix = {}

    for sent, f_table in freq_matrix.items():
        idf_table = {}

        for word in f_table.keys():
            idf_table[word] = math.log10(total_documents / float(count_doc_per_words[word]))

        idf_matrix[sent] = idf_table

    return idf_matrix


def _create_tf_idf_matrix(tf_matrix, idf_matrix):
    tf_idf_matrix = {}

    for (sent1, f_table1), (sent2, f_table2) in zip(tf_matrix.items(), idf_matrix.items()):

        tf_idf_table = {}

        for (word1, value1), (word2, value2) in zip(f_table1.items(),
                                                    f_table2.items()):  # here, keys are the same in both the table
            tf_idf_table[word1] = float(value1 * value2)

        tf_idf_matrix[sent1] = tf_idf_table

    return tf_idf_matrix


def _score_sentences(tf_idf_matrix) -> dict:
    """
    score a sentence by its word's TF
    Basic algorithm: adding the TF frequency of every non-stop word in a sentence divided by total no of words in a sentence.
    :rtype: dict
    """

    sentenceValue = {}

    for sent, f_table in tf_idf_matrix.items():
        total_score_per_sentence = 0

        count_words_in_sentence = len(f_table)
        for word, score in f_table.items():
            total_score_per_sentence += score

        sentenceValue[sent] = total_score_per_sentence / count_words_in_sentence

    return sentenceValue


def _find_average_score(sentenceValue) -> int:
    """
    Find the average score from the sentence value dictionary
    :rtype: int
    """
    sumValues = 0
    for entry in sentenceValue:
        sumValues += sentenceValue[entry]

    # Average value of a sentence from original summary_text
    average = (sumValues / len(sentenceValue))

    return average


def _generate_summary(sentences, sentenceValue, threshold):
    sentence_count = 0
    summary = ''

    for sentence in sentences:
        if sentence[:15] in sentenceValue and sentenceValue[sentence[:15]] >= (threshold):
            summary += " " + sentence
            sentence_count += 1

    return summary


@app.route('/home',methods=['GET','POST'])
@app.route('/',methods=['GET','POST'])
def home():
	if request.method=='POST':
		paragraph=request.form.get('paragraph')
		if paragraph:
			if request.form['button']=='Generate Summary':
				word_frequency= {}
				ps=PorterStemmer()
				tokenizer=word_tokenize(paragraph)

				for word in tokenizer:
				    word=ps.stem(word)
				    if word not in stopwords.words('english'):
				        if word not in word_frequency:
				            word_frequency[word]=1
				        else:
				            word_frequency[word]+=1
				    else:
				        continue

				#lets break the paragraph into the sentences 

				sentence_list=sent_tokenize(paragraph)

				#print(sentence_list)
				sentence_strengths={}

				for sentence in sentence_list:
				    total_words=len(word_tokenize(sentence))
				    for word in word_frequency:
				        if word in sentence.lower():
				            if sentence[0:15] in sentence_strengths:
				                sentence_strengths[sentence[:15]]+=word_frequency[word]
				            else:
				                sentence_strengths[sentence[:15]]=word_frequency[word]
				    sentence_strengths[sentence[:15]]=sentence_strengths[sentence[:15]]//total_words
				                
				## finding the threshold value for summarization
				sum_of_values=0
				for sentence in sentence_strengths:
				    sum_of_values+=sentence_strengths[sentence]
				threshold=sum_of_values//len(sentence_strengths)
				#print(threshold)


				# generating the summary
				sentence_count=0
				summary=''

				for sentence in sentence_list:
				    if sentence[:15] in sentence_strengths and sentence_strengths[sentence[:15]]>threshold:
				        summary+=sentence
				        sentence_count+=1

				
				'''sentences = sent_tokenize(paragraph)
				total_documents = len(sentences)
				#print(sentences)

				# 2 Create the Frequency matrix of the words in each sentence.
				freq_matrix = _create_frequency_matrix(sentences)
				#print(freq_matrix)

				# 3 Calculate TermFrequency and generate a matrix
				tf_matrix = _create_tf_matrix(freq_matrix)
				#print(tf_matrix)

				# 4 creating table for documents per words
				count_doc_per_words = _create_documents_per_words(freq_matrix)
				#print(count_doc_per_words)

				# 5 Calculate IDF and generate a matrix
				idf_matrix = _create_idf_matrix(freq_matrix, count_doc_per_words, total_documents)
				#print(idf_matrix)

				# 6 Calculate TF-IDF and generate a matrix
				tf_idf_matrix = _create_tf_idf_matrix(tf_matrix, idf_matrix)
				#print(tf_idf_matrix)

				# 7 Important Algorithm: score the sentences
				sentence_scores = _score_sentences(tf_idf_matrix)
				#print(sentence_scores)

				# 8 Find the threshold
				threshold = _find_average_score(sentence_scores)
				#print(threshold)

				# 9 Important Algorithm: Generate the summary
				summary = _generate_summary(sentences, sentence_scores, 1.3 * threshold)'''
				return render_template('summary.html',summary=summary)
			
			elif request.form['button']=='Generate Title':
				word_frequency= {}
				ps=PorterStemmer()
				tokenizer=word_tokenize(paragraph)

				for word in tokenizer:
				    word=ps.stem(word)
				    if word not in stopwords.words('english') and word not in [',','/','.','"',"'"]:
				        if word not in word_frequency:
				            word_frequency[word]=1
				        else:
				            word_frequency[word]+=1
				    else:
				        continue
				count=0
				title=[]
				for k,v in sorted(word_frequency.items(),key=lambda item:item[1]): 
					if count==10:
						break
					else:
						title.append(k)
				title=sorted(title)
				if title[0].lower() in ['i','we','myself','our']:
					title='It looks like a biography of author.'
				return render_template('summary.html',summary=title)
		else:
			flash('You forgot something!!')

	return render_template ('home.html')


@app.route('/About')
def about():
    return render_template('About.html')




if __name__=="__main__":
	app.run(debug=True)