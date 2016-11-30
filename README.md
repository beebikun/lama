# lama
lama eats hay and give clean data for lamedoc

### usage

`pythin run.py lich wiki`

-----------------------------------

`python run.py clean wiki -f [raw|a|b] [-to [a|b|c]] [-s num] [-e num]`
where:
* -f - from format
* -to - to format
* -s - num of file to start
* -e - num of file to end

clean levels:
* a - no inner noise
* b - no headers, no repeated
* c - insert tags, no repeated

-----------------------------------

`python run.py split wiki [-c num] [-v num] [-parts percent,percent,...] [-type [a|b|c]]`
* -c - count of files: it will be c files the same size
* -v - volume of filex: here will be x files with v strings in each
* -parts - split file to parts of given percentage. if sum of all percentage != 100, here will be one more file
* -stype - source type of file to split. default c
