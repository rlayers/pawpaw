## From

* [stackoverflow question 76453312](https://stackoverflow.com/questions/76453312/extract-information-from-a-list-of-files-and-write-into-a-log-file)

## Description

Given one or more files that look like this:

```text
MODEL 1
REMARK minimizedAffinity -7.11687565
REMARK CNNscore 0.573647082
REMARK CNNaffinity 5.82644749
REMARK  11 active torsions:
#Lots of text here
MODEL 2
REMARK minimizedAffinity -6.61898327
REMARK CNNscore 0.55260396
REMARK CNNaffinity 5.86855984
REMARK  11 active torsions:
```

Generate output as log file containing "MODEL", "minimizedAffinity", "CNNscore", and "CNNaffinity" of each and every compound in the folder in a delimited text file:

```text
Compound Model minimizedAffinity CNNscore CNNaffinity 
1 1 -7.11687565 0.573647082 5.82644749
1 2 -6.61898327 0.55260396 5.86855984
```
