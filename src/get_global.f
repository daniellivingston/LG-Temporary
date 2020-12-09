      subroutine get_global(ioption,iout,rout,cout,
     *                        itype,ierror_return)
C
C
C#######################################################################
C
C     PURPOSE -
C
C        This routine returns global information.
C
C     INPUT ARGUMENTS -
C
C        ioption   - (character) The variable to be matched.
C
C     OUTPUT ARGUMENTS -
C
C        iout          - The data to be returned.
C        rout          - (real)
C        cout          - (character)
C        itype         - The type of the data to be returned (I=1,R=2,C=3).
C        ierror_return - Error Return Code (==0 ==> OK, <>0 ==> Error).
C
C     CHANGE HISTORY -
C
C        $Log: get_global.f,v $
C        Revision 2.00  2007/11/05 19:45:56  spchu
C        Import to CVS
C
CPVCS    
CPVCS       Rev 1.0   25 Jan 2000 15:41:26   dcg
CPVCS    Initial revision.
C#######################################################################
C
      implicit none
C
C#######################################################################
C
      include 'global_lg.h'
C
C#######################################################################
C
      character*(*) ioption
      character*32 partname,cout
C
      integer  iout, itype, lenout
      real*8 rout
C
      integer ierror_return
C
C#######################################################################
C
C     LOCAL VARIABLE DEFINITION
C
      integer i, len,  icscode
C
      character*132 logmess

C
C#######################################################################
C
C.... Search table for global varible
C
      iout=0
      rout=0.
      cout=' '
      ierror_return=1
      partname='global_lg'
      call mmfindbk('global_name',partname,ipglobal_name,len,icscode)
      call mmfindbk('global_type',partname,ipglobal_type,len,icscode)
      call mmfindbk('global_index',partname,ipglobal_index,len,icscode)
      do i=1,number_of_globals
         if(ioption.eq.global_name(i)) then
            itype=global_type(i)
            if(itype.eq.1) then
               call mmfindbk('global_integer',partname,
     *            ipglobal_integer,len,icscode)
               iout=global_integer(1,global_index(i))
               ierror_return=0
               go to 9999
            elseif(itype.eq.2) then
               call mmfindbk('global_real',partname,ipglobal_real,
     *            len,icscode)
               rout=global_real(1,global_index(i))
               ierror_return=0
               go to 9999
            elseif(itype.eq.3) then
               call mmfindbk('global_character',partname,
     *            ipglobal_character,len,icscode)
               cout=global_character(1,global_index(i))
               ierror_return=0
               go to 9999
            endif
         endif
      enddo
      if(ierror_return.ne.0) then
         itype=-1
         write(logmess,9000) ioption
         call writloga('default',0,logmess,0,icscode)
 9000    format('cannot find global variable : ',a32)
C
      endif
C
 9999 return
      end
