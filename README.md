# imgswap

Create local copies of media in HTML documents and rewrite documents with the local media

## Example
```console
$ cat in.html 
<html><body><img src="https://i.redd.it/ueavss99jvba1.jpg"/></body></html>
$ imgswap.py in.html out.html
64e4a0ed55dcd38b962d5a8af6e6428be6550aea1908a282c88b3ffdc6898805.jpg: from remote
Wrote new document to out.html
1 new media fetched, 0 duplicate media inserted, 0 media inaccessable
$ cat out.html 
<html><body><img data-imgswap-src="https://i.redd.it/ueavss99jvba1.jpg" src="imgswap_media/64e4a0ed55dcd38b962d5a8af6e6428be6550aea1908a282c88b3ffdc6898805.jpg"/></body></html>
```
