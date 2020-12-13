import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.svm import SVC
import seaborn as sn
from sklearn.feature_selection import RFE
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import ShuffleSplit
from sklearn.model_selection import cross_val_score
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import roc_auc_score, log_loss, balanced_accuracy_score ,precision_score, recall_score,f1_score, make_scorer

merged = pd.read_csv('../data/TCGA+GEO.ML_DEGs.tsv.gz', sep='\t', index_col=[0])
#merged = merged[['GSE' in i for i in merged['batch']]]
print('GSE+TCGA')

merged = merged[(merged['Sample_label']!='Primary Normal') & (merged['Sample_label']!='Metastasis Normal')]
X_train = merged[merged['Sample_label']=='Primary Tumor'].iloc[:,:-4]
y_train = merged[merged['Sample_label']=='Primary Tumor'].iloc[:,-4]
X_test = merged[merged['Sample_label']=='Metastasis Tumor'].iloc[:,:-4]
y_test = merged[merged['Sample_label']=='Metastasis Tumor'].iloc[:,-4]

# function adapted from https://medium.com/@aneesha/svm-parameter-tuning-in-scikit-learn-using-gridsearchcv-2413c02125a0
def svc_param_selection(X, y):
    Cs = np.arange(0.5, 11)
    gammas = np.arange(0.001, 0.01, 0.001)
    param_grid = {'C': Cs, 'gamma' : gammas}
    ss = ShuffleSplit(n_splits=10, test_size=0.25, random_state=0)
    grid_search = GridSearchCV(SVC(kernel='rbf'), param_grid, cv=ss)
    grid_search.fit(X, y)
    grid_search.best_params_
    return grid_search.best_params_

best_params = svc_param_selection(X_train, y_train)
print(best_params)

scoring_methods = ['accuracy', 'balanced_accuracy', \
make_scorer(log_loss, needs_proba=True, labels=y_train), \
make_scorer(f1_score, average='weighted'), \
make_scorer(precision_score, average='weighted'), \
make_scorer(recall_score, average='weighted')]
#make_scorer(roc_auc_score, needs_proba=True, average='weighted', multi_class='ovr')]

for m in scoring_methods:
	c = best_params['C']
	gam = best_params['gamma']
	svc = SVC(class_weight='balanced', C=c, gamma=gam, probability=True)
	ss = ShuffleSplit(n_splits=30, test_size=0.25, random_state=0)
	scores = cross_val_score(svc, X_train, y_train, cv=ss, scoring=m)
	print("method\t", m)
	print("mean\t", scores.mean())
	print("STD\t", scores.std()*2)


svc = SVC(class_weight='balanced', C=c, gamma=gam, probability=True)
svc.fit(X_train, y_train)
Y_pred = svc.predict_proba(X_test)

Y_pred_classes = []
for i in Y_pred:
    Y_pred_classes.append(svc.classes_[np.where(i == np.max(i))][0])

print("External validation")
print("roc_auc_score\t", roc_auc_score(y_test, Y_pred, average='weighted', multi_class='ovo'))
print("log_loss\t", log_loss(y_test, Y_pred))
print("precision_score\t", precision_score(y_test, Y_pred_classes, average='weighted'))
print("f1_score\t", f1_score(y_test, Y_pred_classes, average='weighted'))
print("recall_score\t", recall_score(y_test, Y_pred_classes, average='weighted'))

labels = np.union1d(y_test, Y_pred_classes)
cm = pd.DataFrame(confusion_matrix(y_test, Y_pred_classes, labels=labels, normalize='true'), columns = labels, index=labels)

#print("test accuracy:", accuracy_score(y_test, Y_pred))
plt.rcParams.update({'font.size': 12})
sn.heatmap(cm, annot=True, annot_kws={"size":8})
plt.savefig('./confusion_matrix_GSE+TCGA.svg', bbox_inches='tight')


