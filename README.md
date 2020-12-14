# cancifier

The notebook preprocess.ipynb contains the code that was used to preprocess and normalize the data. The following steps were taken to preprocess the data:

- Mapping of Affymetrix microarray probes to the corresponding gene names. The mapping was done using the DAVID tool at https://david.ncifcrf.gov.
  
- Quantile normalization and scaling to zero mean and unit variance. This was done separately for healthy and tumor samples, because quantile normalization assumes the same distribution of each sample, and the expression profiles of healthy and tumor tissues are rarely similar. The general idea behind this step is to remove inter-dataset variation and capture mean-variance relationships within each dataset

- Feature selection for better model performance and faster computational times. Since the majority of genes are housekeeping genes, not all of the genes present in the dataset will be useful in distinguishing between different tissues. Therefore, we performed differential gene expression analysis to select only features useful for subsequent machine learning steps. To select differentially expressed genes (genes that are expressed in one tissue, but not the others), we selected genes by computing the differential gene expression (p<0.05) in each subtype in comparison with the other subtypes of the same cancer type as was outlined by Zhao et al., 2020. Bonferroni correction was used to avoid spurious positives, and a more conservative p-value was used to avoid filtering out some potentially useful features. 
  
- Principal component analysis was used to analyze the effectiveness of preprocessing. Ideally,  the data should segregate in PCA by tissue type, but the batch effect is known to be a confounding variable. Therefore, we included batch as a covariate to check whether our preprocessing successfully removed batch effect and wether true variation has been preserved.
  
- t-SNE was performed on reduced data to further investigate the batch effect. 20 principal components were used rather than original dataset. This is recommended when the number of features is large to suppress some noise and speed up the computation of pairwise distances between samples.

The code in ML.py was used to train and test the SVC model on the preprocessed data.

parse_geo_data.py was used to fetch and merge datasets from GEO database. The resulting dataframe was then read directly into the preprocess.ipynb notebook.
