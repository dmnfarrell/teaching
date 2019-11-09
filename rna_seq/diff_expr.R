#load library
library(edgeR)
#setwd('/storage/mgen_paper_kerri/results/')

#load data
counts <- read.table("final_counts.csv",header=TRUE,sep=',',row.names = 1)
grps <- c(rep("mbovis", 6), rep("mtb", 6))

print(grps)
head(counts)
#Put the counts and other information into a DGEList object to be passed to the edgeR functions
data <- DGEList(counts=counts, group=grps)

data$samples

#Compute effective library sizes that adjust for RNA composition
data <-  calcNormFactors(data)

#An MDS plots shows "distances" between the samples, in terms of biological coefficient of variation (BCV)
plotMDS(data)

#The common dispersion estimates the overall dispersion of the dataset, averaged over all genes
data <- estimateCommonDisp(data, verbose=TRUE)

#Now estimate gene-specific dispersions
data <- estimateTagwiseDisp(data)

plotBCV(data)
#Compute exact genewise tests for differential expression between groups
res <- exactTest (data)

#Report the most significant genes
top <- topTags (res,n = 20)
top

#head(res$table)

write.csv(res$table,file='de_genes.csv')

#plotSmear(res)
#abline(h=c(-1,1), col='blue')

with(res, plot(logFC, -log10(FDR), pch=20, main="KO vs WT"))

#All significant genes
padj <- p.adjust (res$table$PValue, "BH")
touse <- padj < 0.05
table (touse)
res[touse,]$table
