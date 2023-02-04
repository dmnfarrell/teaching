#assignment 2 student expenditure

#use a library called dpylr
library('dplyr')

#set the current working directory - needs to be set to your own folder
setwd('~/gitprojects/teaching/actuarial/')
#read the csv file into a variable called df - this is a data.frame
df <- read.table('student_expenditure.csv',sep=',',header=TRUE,comment.char="")

#frequency of types of purchase
table(df['Food.Personal.School'])

#frequency of cash/cred card
table(df['Cash.Credit.Card'])

#aggregate amount spent per week using dpylr group_by
weeklyamt = df %>% group_by(Week)  %>% summarise(total = sum(Amount))
print (weeklyamt)
#plot this as a bar plot
barplot(weeklyamt$total, names.arg=weeklyamt$Week, 
        xlab='week',main='Weekly expenditure',ylab='amount')

#amount spent monthly
monthlyamt = df %>% group_by(Month)  %>% summarise(total = sum(Amount))
barplot(monthlyamt$total, names.arg=monthlyamt$Month, 
        xlab='month',main='Monthly expenditure')

