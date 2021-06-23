# ModifyPhotoTimeStamp

- Convert the image in the png format to jpg (because I tried to save the information to the png file but found that the png file could not hold it) while ensuring the quality as much as possible.  
- Check whether the jpg file itself contains EXIF information. If it includes, it will not be processed.  
- If the jpg file does not include the EXIF information, the file modification date and the earliest time in the creation date will be used as the time recorded by EXIF and then written into EXIF.  

