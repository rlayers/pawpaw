## From

* [stackoverflow question 47982949](https://stackoverflow.com/questions/47982949/how-to-parse-complex-text-files-using-python)

* [codereview question 183668](https://codereview.stackexchange.com/questions/183668/parse-complex-text-files-using-python)

## Description

Given the a file containing this text:

```text
School = Riverdale High
Grade = 1
Student number, Name
0, Phoebe
1, Rachel

Student number, Score
0, 3
1, 7

Grade = 2
Student number, Name
0, Angela
1, Tristan
2, Aurora

Student number, Score
0, 6
1, 3
2, 9

School = Hogwarts
Grade = 1
Student number, Name
0, Ginny
1, Luna

Student number, Score
0, 8
1, 7

Grade = 2
Student number, Name
0, Harry
1, Hermione

Student number, Score
0, 5
1, 10

Grade = 3
Student number, Name
0, Fred
1, George

Student number, Score
0, 0
1, 0
```

Parset the file and create a pandas DataFrame whose output is as follows:

```text
                                         Name  Score
School         Grade Student number                 
Hogwarts       1     0                  Ginny      8
                     1                   Luna      7
               2     0                  Harry      5
                     1               Hermione     10
               3     0                   Fred      0
                     1                 George      0
Riverdale High 1     0                 Phoebe      3
                     1                 Rachel      7
               2     0                 Angela      6
                     1                Tristan      3
                     2                 Aurora      9
```