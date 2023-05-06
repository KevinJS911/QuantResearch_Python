#Reading csv file
combined_data<- read.csv("C:\\Users\\kevin\\OneDrive\\WORK\\LONDON BUSINESS SCHOOL\\Business Project (Research)\\Code\\Output_Files\\Output_SPX_TR.csv")

#Creating Regression Line & Spline 
combined_data$LowerBound2=combined_data$LowerBound^2
lin_mod<- lm(ExcessReturns ~LowerBound, data= combined_data)
summary(lin_mod)

poly_mod<-lm(ExcessReturns ~poly(LowerBound,2), data= combined_data)
summary(poly_mod)

#Scatter plot
plot(combined_data$LowerBound,combined_data$ExcessReturns, pch=20, col="black", xlab = "Lower Bound", ylab = "Excess Returns", title("Excess Returns v/s Lower Bound"))
#abline(lin_mod, col = "blue")
combined_data$fitted=poly_mod$fitted.values
points(combined_data$LowerBound,combined_data$fitted, col="red", pch=20)

