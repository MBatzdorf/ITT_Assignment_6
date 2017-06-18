import matplotlib
import pandas
import pylab as pl
from scipy.stats import ttest_ind

try:
    # import the data
    data = pandas.read_csv('stats_data.csv', delimiter=';')
    # select only the relevant columns
    data = data[['user_id', 'presented_sentence', 'transcribed_sentence', 'text_input_technique', 'total_time (ms)',
                 'wpm', 'timestamp (ISO)']]
except Exception:
    print("Error! Maybe you need to install pandas!")


data_chord_input = data[data['text_input_technique'] == 'C']
