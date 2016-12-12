# MinHash lyric deduplication
## Music lyrics deduplication using MinHash Locality Sensitive Hashing

This project implements a deduplication technique using *Locality Sensitive Hashing*. 

## Requirements
This project requires python 3, plus the additional packages listed below:

* package dataskecth
* package editdistance
* package pickle

These packages may be installed using your OS package manager or pip3


```sh
pip3 install datasketch editdistance pickle -U
```

## Order of the scripts
First the crawler scripts must be run in order to obtain some data to process.

## References

[Crawler](http://www.michaelnielsen.org/ddi/how-to-crawl-a-quarter-billion-webpages-in-40-hours/)

[Python MinHash LSH](https://github.com/ekzhu/datasketch)
