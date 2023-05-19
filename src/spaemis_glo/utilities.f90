!-----------------------------------------------------------------------------|
!> Data and parameters used to build a population-based anthropogenic inventory
!> @author
!> Martin Cope CSIRO
! Modifications
! When        Who    What
! 31/03/2021  mec    Changed header output
! 02/03/2021  mec    Added MEOH as a mapped VOC species
! 26/09/2018  mec    Corrected pointer to apg species
! 24/08/2018  mec    Added in GLOMAP species
!-----------------------------------------------------------------------------|
MODULE aus_inv
IMPLICIT NONE
SAVE
PUBLIC
!-----------------------------------------------------------------------------|
! Data for National population scaled inventory
!  including mv chemical/temporal emission profiles
!-----------------------------------------------------------------------------|
INTEGER :: nx
INTEGER :: ny
!
REAL :: x0   !corner of sw cell
REAL :: y0
REAL :: dx   !cell width
REAL :: dy
!
INTEGER, PARAMETER :: majorSpecies=6
INTEGER, PARAMETER :: lNOx=1
INTEGER, PARAMETER :: lCO=2
INTEGER, PARAMETER :: lSO2=3
INTEGER, PARAMETER :: lPM10=4
INTEGER, PARAMETER :: lVOC=5
INTEGER, PARAMETER :: lNH3=6
!
CHARACTER(LEN=256) :: gse_filename

!-----------------------------------------------------------------------------|
! Currently one source group
! Src group 1 = gse
!-----------------------------------------------------------------------------|
INTEGER, PARAMETER :: nSrc=1
INTEGER, PARAMETER :: iSRC=nSrc !source indice
INTEGER, PARAMETER :: gse=1

!-----------------------------------------------------------------------------|
! Emission factors- NOx, VOC, CO, SO2, NH3
!    (generally kg/yr/cell -> kkg/day/cell)
! Mapping to spatial factor columns
!-----------------------------------------------------------------------------|
REAL :: NOx_f
REAL :: VOC_f
REAL :: PM_f
REAL :: CO_f
REAL :: SO2_f
REAL :: NH3_f
!
INTEGER :: NOx_c
INTEGER :: VOC_c
INTEGER :: PM_c
INTEGER :: CO_c
INTEGER :: SO2_c
INTEGER :: NH3_c

!-----------------------------------------------------------------------------|
! Speciation and diurnal profiles have been derived from the NSW EPA inventory
! Emission factors- NOx (g-species/g-NOx (as NO2)
!-----------------------------------------------------------------------------|
INTEGER, PARAMETER :: nNOx=2
REAL, DIMENSION(nNOx,nSrc) :: NOx_splt
INTEGER, DIMENSION(nNOx) :: mapNOx = (/1,2/)

!-----------------------------------------------------------------------------|
! Emission factors- VOC
!-----------------------------------------------------------------------------|
INTEGER, PARAMETER :: nVOC=13
REAL, DIMENSION(nVOC,nSrc) :: VOC_splt
INTEGER, DIMENSION(nVOC) :: mapVOC = (/8,19,6,10,11,12,13,20,9,7,18,14,15/)
!INTEGER, DIMENSION(nVOC) :: mapVOC = (/10,19,11,12,13,8,6,20,9,7,18,15,14/)

!-----------------------------------------------------------------------------|
! Emission factors- PM
!-----------------------------------------------------------------------------|
INTEGER, PARAMETER :: nPM=8
REAL, DIMENSION(nPM,nSrc) :: PM_splt
INTEGER, DIMENSION(nPM)  :: mapPM =  (/21,22,23,24,25,26,27,28/)

!-----------------------------------------------------------------------------|
! Emission factors- TOX and levo
!-----------------------------------------------------------------------------|
INTEGER, PARAMETER :: nTOX=4
REAL, DIMENSION(nTOX,nSrc) :: TOX_splt
INTEGER, DIMENSION(nTOX) :: mapTOX = (/38,39,40,41/)

!-----------------------------------------------------------------------------|
! Additional mapping from to standard output species
!-----------------------------------------------------------------------------|
INTEGER, PARAMETER :: mapSO2 = 4
INTEGER, PARAMETER :: mapCO = 3
INTEGER, PARAMETER :: mapNH3 = 17

!-----------------------------------------------------------------------------|
! Temporal emissions profile (in LST)
!-----------------------------------------------------------------------------|
REAL, DIMENSION(0:23,nSrc) :: temporal

!-----------------------------------------------------------------------------|
! Species and molecular weights for output to the gse file
!  - CB05 species; then aer species
! Note that these match the species in the GMR emissions inventory
!-----------------------------------------------------------------------------|
INTEGER, PARAMETER :: nems=41
CHARACTER(LEN=4), DIMENSION(nems) :: name_ems=(/&
        'NO  ','NO2 ','CO  ','SO2 ','PART',     &
        'PAR ','ETH ','OLE ','ISOP','TOL ',     &
        'XYL ','HCHO','ALD2','MEOH','ETOH','NR  ',&
        'NH3 ','ETHA','IOLE','ALDX','OC25',    &
        'OC10','EC25','EC10','OT25','OT10',    &
        'ASO4','AS10','APA1','APA2','APA3',    &
        'APA4','APA5','APA6','APA7','APA8',    &
        'APA9','PTOL','PXYL','PBNZ','LEVO' /)

REAL, DIMENSION(nems) :: mw=(/     &
       30.0,46.0,28.0,64.0,1.0,    &
       14.0,28.0,24.0,68.0,92.0,   &
       106.0,30.0,44.0,34.0,50.0,14.0, &
       17.,30.1,48.,44.,1.,  &
       1.,1.,1.,1.,1.,             &
       1.,1.,1.,1.,1.,             &
       1.,1.,1.,1.,1.,             &
       1.,92.0,106.0,78.1,1./)

!-----------------------------------------------------------------------------|
! GLOMAP species definitions
!-----------------------------------------------------------------------------|
INTEGER, PARAMETER :: nglo=24
CHARACTER(LEN=4), DIMENSION(nglo), PARAMETER :: name_glo  =(/  &
        'SU1 ','SU2 ','SU3 ','SU4 ',           &
        'BC5 ','PO5 ',                         &
        'DU6 ','DU7 ',                         &
        'APG1','APG2','APG3','APG4','APG5',    &
        'APG6','APG7','APG8','APG9',           &
        'NUCS','AITS','ACCS','COAS','AITI','ACCI','COAI'  /)

!-----------------------------------------------------------------------------|
! MWs (g/mole) of SOA precursors and relevant GLOMAP ptcl components and modes
!-----------------------------------------------------------------------------|
REAL, DIMENSION(nGLO), PARAMETER :: mw_glo =(/ &
       98.0,98.0,98.0,98.0,        &
       12.0,16.8,   &                  !BC5 + PO5
       100.,100.,   &                  !DU6 + DU7
       250.,250.,250.,250.,250.,   &   !APG species
       250.,250.,250.,250.,        &   !APG species
       1.0,1.0,1.0,1.0,1.0,1.0,1.0 &   !number density
          /)

!-----------------------------------------------------------------------------|
! Indices pointing to modes for a 7-mode GLOMAP configuration
!-----------------------------------------------------------------------------|
INTEGER, PARAMETER :: modes=7
INTEGER, PARAMETER :: NUCS=1  !nucln. soluble
INTEGER, PARAMETER :: AITS=2  !Aitken soluble
INTEGER, PARAMETER :: ACCS=3  !accum. soluble
INTEGER, PARAMETER :: COAS=4  !coarse soluble
INTEGER, PARAMETER :: AITI=5  !Aitken insoluble
INTEGER, PARAMETER :: ACCI=6  !accum. insoluble
INTEGER, PARAMETER :: COAI=7  !coarse insoluble
CHARACTER(LEN=4), DIMENSION(modes) :: mode_nm=(/'nucs','aits','accs','coas',  &
                                                       'aiti','acci','coai'/)
INTEGER, DIMENSION(modes)  :: l_nd = (/18,19,20,21,22,23,24/) !mode number density pointer
INTEGER, PARAMETER :: nInv = 3 !VBS categories treated as involatile
REAL :: modevol
REAL :: lgsd
REAL, PARAMETER :: ppi=3.141592654

!-----------------------------------------------------------------------------|
!          h2so4  bc     oc    nacl   dust    so
! n.b. mm_bc=0.012, mm_oc=0.012*1.4=0.168 (1.4 C-H ratio)
! Mass density of components (kg m^-3)
!-----------------------------------------------------------------------------|
INTEGER, PARAMETER :: ncp=6
REAL, DIMENSION(ncp) :: rhocomp=(/1769.0,1500.0,1500.0,1600.0,2650.0,1500.0/)
INTEGER, PARAMETER :: su_p=1
INTEGER, PARAMETER :: bc_p=2
INTEGER, PARAMETER :: oc_p=3
INTEGER, PARAMETER :: ss_p=4
INTEGER, PARAMETER :: du_p=5
INTEGER, PARAMETER :: so_p=6

!-----------------------------------------------------------------------------|
! Size distribution particle definitions
! -Sulfate (nucl, aits, accs, coas)
!-----------------------------------------------------------------------------|
   INTEGER :: n_su                                !number of modes
   INTEGER, ALLOCATABLE, DIMENSION(:) :: m_su     !mode number
   REAL, ALLOCATABLE, DIMENSION(:) :: d_su        !geometric mean diameter (nm)
   REAL, ALLOCATABLE, DIMENSION(:) :: gsig_su     !geometric standard deviation
   REAL, ALLOCATABLE, DIMENSION(:) :: f_su        !fraction in each mode
   INTEGER, DIMENSION(modes) :: l_su = (/1,2,3,4,-1,-1,-1/) !sulfate component pointers

!-----------------------------------------------------------------------------|
! Size distribution particle definitions
! -OC and EC (aiti)
!-----------------------------------------------------------------------------|
   INTEGER :: n_ecoc                            !number of modes
   INTEGER, ALLOCATABLE, DIMENSION(:) :: m_ecoc !mode number
   REAL, ALLOCATABLE, DIMENSION(:) :: d_ecoc    !geometric mean diameter (nm)
   REAL, ALLOCATABLE, DIMENSION(:) :: gsig_ecoc !geometric standard deviation
   REAL, ALLOCATABLE, DIMENSION(:) :: f_ecoc    !fraction in each mode
   REAL, DIMENSION(modes) :: oc !oc emissions (g/s)
   INTEGER, DIMENSION(modes) :: l_bc = (/-1,-1,-1,-1,5,-1,-1/) !bc component pointers
   INTEGER, DIMENSION(modes) :: l_oc = (/-1,-1,-1,-1,6,-1,-1/) !oc component pointers

!-----------------------------------------------------------------------------|
! Size distribution particle definitions
! -other (dust; metals) (acci,coai)
!-----------------------------------------------------------------------------|
   INTEGER :: n_du                              !number of modes
   INTEGER, ALLOCATABLE, DIMENSION(:) :: m_du   !mode number
   REAL, ALLOCATABLE, DIMENSION(:) :: d_du      !geometric mean diameter (nm)
   REAL, ALLOCATABLE, DIMENSION(:) :: gsig_du   !geometric standard deviation
   REAL, ALLOCATABLE, DIMENSION(:) :: f_du      !fraction in each mode
   INTEGER, DIMENSION(modes) :: l_du = (/-1,-1,-1,-1,-1,7,8/) !dust component s

!-----------------------------------------------------------------------------|
! Speciation of OC into VBS OM (CSIRO)
!-----------------------------------------------------------------------------|
INTEGER, PARAMETER :: nvbs = 9
REAL, DIMENSION(nvbs,nSrc) :: vbs
!
INTEGER, PARAMETER :: loc25=21
INTEGER, PARAMETER :: loc10=22
INTEGER, PARAMETER :: lec25=23
INTEGER, PARAMETER :: lec10=24
INTEGER, PARAMETER :: lot25=25
INTEGER, PARAMETER :: lot10=26
INTEGER, PARAMETER :: lso4=27
INTEGER, PARAMETER :: ls10=28
INTEGER, PARAMETER :: lapa=29

!-----------------------------------------------------------------------------|
!  GLOMAP species and pointers to speciation factors
!-----------------------------------------------------------------------------|
REAL, DIMENSION(nvbs) :: apa
REAL, DIMENSION(nvbs) :: apg
INTEGER, PARAMETER :: lsu1=1
INTEGER, PARAMETER :: lsu4=4
INTEGER, PARAMETER :: lbc5=5
INTEGER, PARAMETER :: lpo5=6
INTEGER, PARAMETER :: ldu6=7
INTEGER, PARAMETER :: ldu7=8
INTEGER, PARAMETER :: lnucs=18
INTEGER, PARAMETER :: laits=19
INTEGER, PARAMETER :: laccs=20
INTEGER, PARAMETER :: lcoas=21
INTEGER, PARAMETER :: laiti=22
INTEGER, PARAMETER :: lacci=23
INTEGER, PARAMETER :: lcoai=24
INTEGER, PARAMETER :: lapg=9
!
REAL, PARAMETER :: kgPhrTogPsec=1000./3600.
REAL, PARAMETER :: hrToSec=1.0/3600.

!-----------------------------------------------------------------------------|
!  Output emissions table and mapping from internal emissions
!-----------------------------------------------------------------------------|
INTEGER :: nems_ot
CHARACTER(LEN=4), ALLOCATABLE, DIMENSION(:) :: name_ems_ot
INTEGER, ALLOCATABLE, DIMENSION(:) :: map_ems
REAL, ALLOCATABLE, DIMENSION(:) :: mpped_mw
END MODULE aus_inv
!
MODULE utilities
IMPLICIT NONE
SAVE
PRIVATE
PUBLIC writeTapm_header,surfer_dump,xyz_dump, &
       juliandaynumber,gregoriandate,qsum,qsum1

CONTAINS
!-------------------------------------------------------------------------------
!  writeTapm_header
!-------------------------------------------------------------------------------
!> Function to write out header data to a C-CTM emissions file
!> @author
!> Martin Cope CSIRO
! Modifications
! When        Who    What
! 07/05 2020  mec    Added user meta data
! 24/08/2018  mec    Added in GLOMAP species
!-------------------------------------------------------------------------------
FUNCTION writeTapm_header(funit,fform,nems,species,mw,  &
                                      nglo,species_glo,mw_glo, &
                                      user_meta)
IMPLICIT NONE
LOGICAL :: writeTapm_header
INTEGER, INTENT(IN) :: funit  !file unit
LOGICAL, INTENT(IN) :: fform  !file unit
INTEGER, INTENT(IN) :: nems !number of inventory species
REAL, DIMENSION(:), INTENT(IN) :: mw                  !molecular weights
CHARACTER(LEN=4), DIMENSION(:), INTENT(IN) :: species !species names
INTEGER, INTENT(IN) :: nglo !number of GLOMAP inventory species
REAL, DIMENSION(:), INTENT(IN) :: mw_glo                  !GLOMAP molecular weights
CHARACTER(LEN=4), DIMENSION(:), INTENT(IN) :: species_glo !GLOMAP species names
CHARACTER(LEN=80), DIMENSION(:), INTENT(IN) :: user_meta  !user information
CHARACTER(LEN=80) :: comment
CHARACTER(LEN=8) :: systemDate
CHARACTER(LEN=10) :: systemTime
INTEGER :: i
writeTapm_header=.FALSE.

!-------------------------------------------------------------------------------
! Generate header for C-CTM vpx/vpv files
!-------------------------------------------------------------------------------
CALL DATE_and_TIME(systemDate,systemTime)
IF(Fform)THEN
  comment='version_02'
  WRITE(funit,ERR=94)comment
  comment='C-CTM surface emissions file. Generated by spaemis_glo software'
  WRITE(funit,ERR=94)comment
  comment='File was created (yyyymmdd): '//systemDate//' at time (hhmmss.sss): '//systemTime
  WRITE(funit,ERR=94)comment
  comment='GramPerSec :C-CTM emission units of g/s'
  WRITE(funit,ERR=94)comment
  comment='Uniform grid'
  WRITE(funit,ERR=94)comment
  DO i =1,SIZE(user_meta)
    WRITE(funit,ERR=94)user_meta(i)
  END DO
  comment='*'
  WRITE(funit,ERR=94)comment
  WRITE(funit,ERR=94)nems+nglo
  DO i=1,nems
    WRITE(funit,ERR=94)i,species(i),mw(i)
  END DO
  DO i=1,nglo
    WRITE(funit,ERR=94)i+nems,species_glo(i),mw_glo(i)
  END DO
ELSE
  WRITE(funit,1,ERR=94)'Version_02'
  WRITE(funit,1,ERR=94)'C-CTM surface emissions file. Generated by PopEmis_GLO software'
1 FORMAT(100a)
  WRITE(funit,1,ERR=94)'File was created (yyyymmdd): ',systemDate,' at time (hhmmss.sss): ',systemTime
  WRITE(funit,1,ERR=94)'GramPerSec :C-CTM emission units of g/s'
  WRITE(funit,1,ERR=94)'Uniform grid'
  DO i =1,SIZE(user_meta)
    WRITE(funit,1,ERR=94)user_meta(i)
  END DO
  WRITE(funit,1,ERR=94)'*'
  WRITE(funit,*,ERR=94)nems+nglo
  DO i=1,nems
    WRITE(funit,2,ERR=94)i,species(i),mw(i)
2   FORMAT(i3,1x,a,1x,F5.1)
  END DO
  DO i=1,nglo
    WRITE(funit,2,ERR=94)i+nems,species_glo(i),mw_glo(i)
  END DO

END IF
writeTapm_header=.TRUE.
RETURN
!-------------------------------------------------------------------------------
! Errors
!-------------------------------------------------------------------------------
94 PRINT *,'Error writing C-CTM header to binary file'
RETURN
END FUNCTION writeTapm_header

!-------------------------------------------------------------------------------
!> Routine dumps out data in Surfer ASCII format
!> @author
!> Martin Cope CSIRO
!-------------------------------------------------------------------------------
SUBROUTINE surfer_dump(iunit,x0,y0,dx,dy,grid,filename)
IMPLICIT NONE
INTEGER, INTENT(IN) :: iunit                !Fortran I/O unit
REAL, INTENT(IN) :: x0,y0,dx,dy             !grid location/size
REAL, INTENT(IN), DIMENSION(:,:) :: grid  !data
CHARACTER(LEN=*), INTENT(IN) :: filename    !output filename
INTEGER :: nx,ny                            !grid dimensions
INTEGER :: j
!
nx=SIZE(grid,1)
ny=SIZE(grid,2)
!
! Open the file unit write out header information
!
OPEN(UNIT=iunit,FILE=TRIM(filename),STATUS='unknown')
!
WRITE(iunit,1)'DSAA'
1 FORMAT(a)
WRITE(iunit,'(i5,1x,i5)')nx,ny
WRITE(iunit,*)x0,(x0+FLOAT(nx-1)*dx)
WRITE(iunit,*)y0,(y0+FLOAT(ny-1)*dy)
WRITE(iunit,*)MINVAL(grid),MAXVAL(grid)
!
DO j=1,ny
  WRITE(iunit,101)grid(:,j)
  101 FORMAT(10(e10.3,1x))
  WRITE(iunit,'()')
END DO
CLOSE(iunit)
END SUBROUTINE surfer_dump
!-------------------------------------------------------------------------------
!> Routine dumps out data in Surfer ASCII format
!> @author
!> Martin Cope CSIRO
!-------------------------------------------------------------------------------
SUBROUTINE xyz_dump(iunit,x0,y0,dx,dy,grid,filename)
IMPLICIT NONE
INTEGER, INTENT(IN) :: iunit                !Fortran I/O unit
REAL, INTENT(IN) :: x0,y0,dx,dy             !grid location/size
REAL, INTENT(IN), DIMENSION(:,:) :: grid  !data
CHARACTER(LEN=*), INTENT(IN) :: filename    !output filename
CHARACTER(LEN=1), PARAMETER:: comma=','
INTEGER :: i,j
INTEGER :: nx,ny                !grid dimensions
REAL :: x,y
nx=SIZE(grid,1)
ny=SIZE(grid,2)
!
! Open the file unit write out header information
!
OPEN(UNIT=iunit,FILE=TRIM(filename),STATUS='unknown')
!
WRITE(iunit,'(a)')'x,y,conc'
!
!  DO i=1,nx
!    x=x0+FLOAT(i-1)*dx
DO j=1,ny
  y=y0+FLOAT(j-1)*dy
  DO i=1,nx
    x=x0+FLOAT(i-1)*dx
    WRITE(iunit,*)x,comma,y,comma,grid(i,j)
  END DO
END DO
CLOSE(iunit)
101 FORMAT(g10.3,2(a,g10.3))
END SUBROUTINE xyz_dump
!-------------------------------------------------------------------------------
!> Routine calculates julian day number
!> @author
!> Martin Cope CSIRO
!-------------------------------------------------------------------------------
FUNCTION JulianDayNumber(y,m,d)
IMPLICIT NONE
INTEGER :: JulianDayNumber
INTEGER, INTENT(IN) :: y !year
INTEGER, INTENT(IN) :: d !day
INTEGER, INTENT(IN) :: m !month

JulianDayNumber = ( 1461 * ( y + 4800 + ( m - 14 ) / 12 ) ) / 4 +   &
                 ( 367 * ( m - 2 - 12 * ( ( m - 14 ) / 12 ) ) ) / 12 - &
                 ( 3 * ( ( y + 4900 + ( m - 14 ) / 12 ) / 100 ) ) / 4 + &
                  d - 32075
END FUNCTION JulianDayNumber
!-------------------------------------------------------------------------------
!> Routine converts from julian day number to Gregorian date
!> @author
!> Martin Cope CSIRO
!-------------------------------------------------------------------------------
FUNCTION GregorianDate(jd)
IMPLICIT NONE
INTEGER, DIMENSION(3) :: GregorianDate
INTEGER, INTENT(IN) :: jd !julian day number
INTEGER :: y,m,d          !year,month,day
INTEGER :: l,n,i,j        !intermediates

l = jd + 68569
n = ( 4 * l ) / 146097
l = l - ( 146097 * n + 3 ) / 4
i = ( 4000 * ( l + 1 ) ) / 1461001
l = l - ( 1461 * i ) / 4 + 31
j = ( 80 * l ) / 2447
d = l - ( 2447 * j ) / 80
l = j / 11
m = j + 2 - ( 12 * l )
y = 100 * ( n - 49 ) + i + l

GregorianDate(1)=y
GregorianDate(2)=m
GregorianDate(3)=d
END FUNCTION GregorianDate
FUNCTION qsum(q,qmap,qmask)
IMPLICIT NONE
REAL :: qsum
REAL, INTENT(IN), DIMENSION(:,:,:)  :: q    !data (kg/day)
INTEGER, INTENT(IN), DIMENSION(:)   :: qmap !emission map
LOGICAL, INTENT(IN), DIMENSION(:,:) :: qmask!emission mask
!
INTEGER :: s,nm
nm=SIZE(qmap)
qsum = 0.0
DO s=1,nm
  qsum = qsum + SUM(q(qmap(s),:,:),qmask)
END DO
END FUNCTION qsum
FUNCTION qsum1(q,qm1,qm2,qmask)
IMPLICIT NONE
REAL :: qsum1
INTEGER, INTENT(IN) :: qm1,qm2
REAL, INTENT(IN), DIMENSION(:,:,:)  :: q    !data (kg/day)
LOGICAL, INTENT(IN), DIMENSION(:,:) :: qmask!emission mask
!
INTEGER :: s,nm
qsum1 = 0.0
DO s=qm1,qm2
  qsum1 = qsum1 + SUM(q(s,:,:),qmask)
END DO
END FUNCTION qsum1
END MODULE utilities
