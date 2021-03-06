# 1 "machine_header.F"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "machine_header.F"
C This file uses compiler preprocess options to set default
C and machine dependent sizes. This include file sets the
C SIZEOF for integer, long, and void pointer
C May need updates to obsolete systems and use of 64 bit sizes
C this replaces "opsys.h" as used in the lg_util library
C and compiles into new version of machine.h

C These settings copied from opsys.h in lg_util library
C              opsys.h

C Default name mangle scheme 




















































# 73 "machine_header.F"

CCCCCCCCCC end opsys.h (((((((((((((((((((((((((((((((((((((((((

C     NBYTES_REAL number of bytes in a real variable
C     NBYTES_INT number of bytes in a integer variable
C             WORKSTATION set NBYTES_REAL = 8, NBYTES_INT = 4
C             CRAY set NBYTES_REAL = 8, NBYTES_INT = 8
C             64 bit integer can be set to 4 or 8
C             LaGriT integer size must be equal to pointer size

      integer NBYTES_REAL, NBYTES_INT
      parameter (NBYTES_REAL = 8, NBYTES_INT = 4)

      integer BYTES_PER_INT, BYTES_PER_REAL
      parameter (BYTES_PER_INT = 4, BYTES_PER_REAL = 8)

      integer BYTES_PER_CHAR
      parameter (BYTES_PER_CHAR = 32)

      integer BYTES_PER_PTR
      parameter (BYTES_PER_PTR = 4) 

CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
C                     System-Dependent Quantities.
C
C     The following machine quantities have been included here
C     and were meant to be set by hand at time of compile
C     These can be updated to be set with preprocess as above

 
C                       CRAY Machine Quantities
C     KNCPW    The number of characters per computer (REAL*8) word.
      INTEGER KNCPW
               PARAMETER (KNCPW = 8)
 
C     KNWPN    The number of computer (REAL*8) words per character name.
      INTEGER KNWPN
               PARAMETER (KNWPN = 4)
 
C     KNCPN    The number of characters per character name.
      INTEGER KNCPN
               PARAMETER (KNCPN = KNCPW * KNWPN)
 
C     KNBPW    The number of bits per computer (REAL*8) word.
      INTEGER KNBPW
               PARAMETER (KNBPW = 64)
 
C                       CTSS System  Quantities
C     KWLSECT  The length in computer words of a disk sector.
      INTEGER KWLSECT
               PARAMETER (KWLSECT = 512)
 
C     nptrfac The multiplier for pointer arithmetic.  i.e for:
C             WORKSTATION set NPTRFAC=8, NPTRFAC_INT=4
C             CRAY        set NPTRFAC=1, NPTRFAC_INT=1
      INTEGER NPTRFAC, NPTRFAC_INT
              parameter (NPTRFAC=8, NPTRFAC_INT=4)
 
 
C                     Optimal Machine Quantities
C     KVECLEN --- Optimal vector length
      INTEGER KVECLEN
              PARAMETER (KVECLEN = 256)
C     nwadr is number of words in a machine address
C
      integer nwadr
      parameter (nwadr=1)
 
C                         ( end  of  machine )
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
