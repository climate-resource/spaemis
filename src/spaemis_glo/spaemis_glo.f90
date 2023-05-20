!-----------------------------------------------------------------------------|
!> Calculate generic anthropogenic emissions for Australia
!> @author
!> mec CSIRO May 2016
! Modifications
! When        Who    What
!28/04/2021   mec  Added masking capability
!31/03/2021   mec  Fixed broken free format read of name,number
!26/03/2021   mec  Fix bug in writing GLOMAP data to .gse file
!23/06/2020   mec  Read in an arbitrary multi-column grid of spatial factors
!14/05/2020   mec  Fixed bug in writing output to .gse file
!07/05/2020   mec  Added user meta data to top of .gse file
!24/08/2018   mec  Added in GLOMAP species
!17/05/2018   mec  All hard-wired data exported into the .run file
!27/07/2017   mec  First version of the code
!-----------------------------------------------------------------------------|
PROGRAM spaemis_glo
USE aus_inv
USE utilities
IMPLICIT NONE
INTEGER, PARAMETER :: iUnit=7
INTEGER, PARAMETER :: dUnit=13
INTEGER, PARAMETER :: sUnit=14
INTEGER, DIMENSION(nSrc) :: Ounit
CHARACTER(LEN=80), DIMENSION(5) :: gse_comment
CHARACTER(LEN=80) :: header
LOGICAL           :: asciiYes !ASCII output?
CHARACTER(LEN=1024) :: filename,fname,spatial_data,line

!-----------------------------------------------------------------------------|
! User defined domain and mapped spatial factors
!-----------------------------------------------------------------------------|
INTEGER :: nx_usr,ny_usr
REAL    :: x0_usr,y0_usr,dx_usr,dy_usr
REAL    :: x_center,y_center
REAL, ALLOCATABLE, DIMENSION(:,:,:) :: spaf_usr !spatial factors in user domain
LOGICAL, ALLOCATABLE, DIMENSION(:,:) :: spaf_usrM !domain mask
REAL, ALLOCATABLE, DIMENSION(:)     :: lat_usr,lon_usr !user domain grid
REAL, ALLOCATABLE, DIMENSION(:,:) :: temp

!-----------------------------------------------------------------------------|
! Variables for the external data set of spatial factors
!-----------------------------------------------------------------------------|
INTEGER :: n_f  !number of spatial emission factor fields
CHARACTER(LEN=80) :: c_har
CHARACTER(LEN=80), ALLOCATABLE, DIMENSION(:) :: hames !header names
REAL :: lat,lon !deg
REAL, ALLOCATABLE, DIMENSION(:) :: spaf_data !generally kg/cell/hr

!-----------------------------------------------------------------------------|
! Emission fields
!-----------------------------------------------------------------------------|
REAL, ALLOCATABLE, DIMENSION(:,:,:) :: emsn         !(g/cell/s)
REAL, ALLOCATABLE, DIMENSION(:,:,:) :: emsn_glo     !(ptcl;g/cell/s)

!-----------------------------------------------------------------------------|
! Miscellaneous
!-----------------------------------------------------------------------------|
INTEGER :: i,j,jd,l,x,y,s,h,k,t,day,jd_lst,iu,ju,v,rec,ios,cma
CHARACTER(LEN=2) :: a
LOGICAL :: done
DO i=1,nSrc
  Ounit(i)=sUnit+i
END DO

!-----------------------------------------------------------------------------|
! Read in name of .gse file
! Get comments for .gse file
!-----------------------------------------------------------------------------|
WRITE(*,*)'Processing spaemis control file'
OPEN(UNIT=iUnit,FILE='spaemis_glo.run',STATUS='old')
READ(iUnit,1)header
READ(iUnit,1)header
READ(iUnit,*)nx_usr,ny_usr,x0_usr,y0_usr,dx_usr,dy_usr
WRITE(*,*)header
!-----------------------------------------------------------------------------|
! Set up arrays
! Set up domains
!-----------------------------------------------------------------------------|
ALLOCATE(emsn(nems,nx_usr,ny_usr))
ALLOCATE(emsn_glo(nglo,nx_usr,ny_usr))
ALLOCATE(lat_usr(ny_usr))
ALLOCATE(lon_usr(nx_usr))
!
DO y=1,ny_usr
  lat_usr(y)=y0_usr+FLOAT(y-1)*dy_usr
END DO
DO x=1,nx_usr
  lon_usr(x)=x0_usr+FLOAT(x-1)*dx_usr
END DO
x_center=(lon_usr(1)+lon_usr(nx_usr))*0.5
y_center=(lat_usr(1)+lat_usr(ny_usr))*0.5
!
READ(iUnit,1)header
WRITE(*,*)header
1 FORMAT(a)
READ(iUnit,19)spatial_data
19 FORMAT(a)
READ(iUnit,*)n_f
WRITE(*,*) "printing fname:",TRIM(spatial_data),n_f

!-----------------------------------------------------------------------------|
!  Read in information/parameters
!-----------------------------------------------------------------------------|
READ(iUnit,1)header
READ(iUnit,1)filename
READ(iUnit,1)header
DO i=1,5
 READ(iUnit,'(a)')gse_comment(i)
END DO
!gse_Comment(6)='*'
READ(iUnit,1)header
READ(iUnit,'(l1)')asciiYes

!-------------------------------------------------------------------------------
! Read in indices to map from internal emission table to
!  user defined emission species
!-------------------------------------------------------------------------------
DO i=1,13
  READ(iUnit,1)header
  write(*,*)header
END DO
READ(iUnit,*)nems_ot
write(*,*)'yes',nems_ot
ALLOCATE(name_ems_ot(nems_ot))
ALLOCATE(map_ems(nems_ot))
ALLOCATE(mpped_mw(nems_ot))
READ(iUnit,1)header
READ(iUnit,1)header
READ(iUnit,*)(name_ems_ot(s),map_ems(s),s=1,nems_ot)
!
WHERE(map_ems(:) == -1)
  map_ems(:)=nems
END WHERE
mpped_mw=mw(map_ems(:))

!-----------------------------------------------------------------------------|
!  Read in a spatial factor data set (generally kg/yr/cell)
!-----------------------------------------------------------------------------|
ALLOCATE(hames(n_f))
ALLOCATE(spaf_data(n_f))
ALLOCATE(spaf_usr(n_f,nx_usr,ny_usr))
ALLOCATE(spaf_usrM(nx_usr,ny_usr))
spaf_usr(:,:,:)=0.0
spaf_usrM(:,:)=.FALSE.
!
WRITE(*,*)'Reading in spatial data: ',TRIM(spatial_data)
OPEN(UNIT=sUnit,FILE=TRIM(spatial_data),STATUS='OLD')
READ(sUnit,1)header
write(*,*)header
Read(header,*)c_har,c_har,hames(1:n_f)
!
rec=0
DO
  READ(sUnit,*,IOSTAT=ios)lon,lat,spaf_data(:)    !factors per cell
  IF(ios /= 0)EXIT
    !spaf_data(:)=MAX(0.,spaf_data(:))
    iu=NINT((lon-x0_usr)/dx_usr+1.0)
    ju=NINT((lat-y0_usr)/dy_usr+1.0)
    IF(ju >=1 .AND. ju <= ny_usr .AND.    &
       iu >=1 .AND. iu <= nx_usr )THEN
      IF(.NOT.MAXVAL(spaf_data(:)) < 0.0)THEN
        spaf_usrM(iu,ju) = .TRUE.
        spaf_usr(:,iu,ju)=spaf_usr(:,iu,ju)+spaf_data(:)
      END IF !mask check
    END IF  !x,y check
    rec=rec+1
END DO !record loop
CLOSE(sUnit)
IF(rec==0)THEN
  PRINT *,'Error no spatial data records in the file: ',TRIM(spatial_data)
  STOP
END IF

!
WRITE(*,*)'Mapping data to user domain, writing diagnostic files'
ALLOCATE(temp(nx_usr,ny_usr))
!temp = RESHAPE(spaf_usr,(/nx_usr,ny_usr,n_f/),ORDER=(/2,3,1/))

DO l=1,n_f
 !WHERE(spaf_usrM)  !causes stackoverflow
 !   temp=spaf_usr(l,:,:)
 !ELSEWHERE
 !   temp=-1.0
 !ENDWHERE
 !temp(1:nx_usr,1:ny_usr)=spaf_usr(l,1:nx_usr,1:ny_usr)
 temp(1:nx_usr,1:ny_usr)=-1.0
 DO y=1,ny_usr
  DO x=1,nx_usr
    IF(spaf_usrM(x,y))temp(x,y)=spaf_usr(l,x,y)
  END DO
 END DO
 CALL surfer_dump(sUnit,x0_usr,y0_usr,dx_usr,dy_usr,    &
                   temp(1:nx_usr,1:ny_usr), &
                   TRIM(hames(l))//'.grd')
END DO !loop over spatial factor columns
DEALLOCATE(temp)

!-----------------------------------------------------------------------------|
! Read in the per spatial unit emission factors (generally kg/yr -> kg/day)
! _f is the factor; _c is the data column
!-----------------------------------------------------------------------------|
WRITE(*,*)'Processing emissions scale factors and speciation data'
READ(iUnit,1)header
write(*,*)"checker1",header
READ(iUnit,1)header
write(*,*)"checker2",header
READ(iUnit,1)header
write(*,*)"checker3",header
READ(iUnit,*)NOx_c,VOC_c,PM_c,CO_c,SO2_c,NH3_c
write(*,*)NOx_c,VOC_c,PM_c,CO_c,SO2_c,NH3_c
READ(iUnit,*)NOx_f,VOC_f,PM_f,CO_f,SO2_f,NH3_f
write(*,*)NOx_f,VOC_f,PM_f,CO_f,SO2_f,NH3_f

!-----------------------------------------------------------------------------|
! Read in NOx speciation factors (e.g. kg/day/capita)
!-----------------------------------------------------------------------------|
READ(iUnit,1)header
READ(iUnit,1)header
READ(iUnit,*)(NOx_splt(s,iSrc),s=1,nNOx)

!-----------------------------------------------------------------------------|
! Read in VOC speciation factors (e.g. kg/day/capita)
!-----------------------------------------------------------------------------|
READ(iUnit,1)header
READ(iUnit,1)header
READ(iUnit,*)(VOC_splt(s,iSrc),s=1,nVOC)
write(*,*)'VOC_split',(VOC_splt(s,iSrc),s=1,nVOC)
!-----------------------------------------------------------------------------|
! Read in PM speciation factors (e.g. kg/day/capita)
!-----------------------------------------------------------------------------|
READ(iUnit,1)header
READ(iUnit,1)header
READ(iUnit,*)(PM_splt(s,iSrc),s=1,nPM)

!-----------------------------------------------------------------------------|
! Read in TOx speciation factors (e.g. kg/day/capita)
!-----------------------------------------------------------------------------|
READ(iUnit,1)header
READ(iUnit,1)header
READ(iUnit,*)(TOX_splt(s,iSrc),s=1,nTOx)

!-----------------------------------------------------------------------------|
! Read in the volatility basis set speciation (9 bins)
!-----------------------------------------------------------------------------|
READ(iUnit,1)header
READ(iUnit,1)header
READ(iUnit,*)(vbs(s,iSrc),s=1,nvbs)

!-------------------------------------------------------------------------------
! GLOMAP parameters
! Sulfate;
!-------------------------------------------------------------------------------
READ(iUnit,1)
READ(iUnit,1)
READ(iUnit,1)
READ(iUnit,1)line
READ(line,*)n_su              !number of modes
ALLOCATE(m_su(MAX(n_su,1)))   !mode numbers
ALLOCATE(d_su(MAX(n_su,1)))   !mode diameter (nm)
ALLOCATE(gsig_su(MAX(n_su,1)))!geometric standard deviation
ALLOCATE(f_su(MAX(n_su,1)))   !mass fraction
IF(n_su > 0)THEN
  READ(line,*)n_su,(m_su(i),d_su(i),gsig_su(i),f_su(i),i=1,n_su)
  DO i=1,n_su
    IF(m_su(i)==-1)THEN
      PRINT *,'Error ', 'the mode ',mode_nm(m_su(i)),  &
              ' is not currently defined for sulfate emissions'
      STOP
    END IF
  END DO
ELSE
  PRINT *,'Error, must define at least 1 sulfate emission mode'
  STOP 'Fatal error'
END IF !sulphate

!-------------------------------------------------------------------------------
! ec/oc;
!-------------------------------------------------------------------------------
READ(iUnit,1)
READ(iUnit,1)
READ(iUnit,1)line
READ(line,*)n_ecoc                !number of modes
ALLOCATE(m_ecoc(MAX(n_ecoc,1)))   !mode numbers
ALLOCATE(d_ecoc(MAX(n_ecoc,1)))   !mode diameter (nm)
ALLOCATE(gsig_ecoc(MAX(n_ecoc,1)))!geometric standard deviation
ALLOCATE(f_ecoc(MAX(n_ecoc,1)))   !mass fraction
IF(n_ecoc > 0)THEN
  READ(line,*)n_ecoc,(m_ecoc(i),d_ecoc(i),gsig_ecoc(i),f_ecoc(i),i=1,n_ecoc)
  DO i=1,n_ecoc
    IF(m_ecoc(i)==-1)THEN
      PRINT *,'Error ', 'the mode ',mode_nm(m_ecoc(i)),  &
              ' is not currently defined for ec/oc emissions'
      STOP
    END IF
  END DO
ELSE
  PRINT *,'Error, must define at least 1 ec/oc emission mode'
  STOP 'Fatal error'
END IF !carbon

!-------------------------------------------------------------------------------
! du;
!-------------------------------------------------------------------------------
READ(iUnit,1)
READ(iUnit,1)
READ(iUnit,1)line
READ(line,*)n_du              !number of modes
ALLOCATE(m_du(MAX(n_du,1)))   !mode numbers
ALLOCATE(d_du(MAX(n_du,1)))   !mode diameter (nm)
ALLOCATE(gsig_du(MAX(n_du,1)))!geometric standard deviation
ALLOCATE(f_du(MAX(n_du,1)))   !mass fraction
IF(n_du > 0)THEN
  READ(line,*)n_du,(m_du(i),d_du(i),gsig_du(i),f_du(i),i=1,n_du)
    DO i=1,n_du
      IF(m_du(i)==-1)THEN
        PRINT *,'Error ', 'the mode ',mode_nm(m_du(i)),  &
            ' is not currently defined for dust emissions'
        STOP
      END IF
    END DO
ELSE
  PRINT *,'Error, must define at least 1 dust emission mode'
  STOP 'Fatal error'
END IF !dust

!-----------------------------------------------------------------------------|
! Read in the normalised temporal emission profile hour_frac/day
!-----------------------------------------------------------------------------|
READ(iUnit,1)header
READ(iUnit,1)header
READ(iUnit,*)(temporal(s,iSrc),s=0,23)
CLOSE(iUnit)

!-----------------------------------------------------------------------------|
! Open .gse file
!-----------------------------------------------------------------------------|
IF(asciiYes)THEN
  fname=TRIM(filename)//'.gse'
  OPEN(oUnit(gse),file=trim(fname), form='formatted')
ELSE
  fname=TRIM(filename)//'.gse.bin'
  OPEN(oUnit(gse),file=trim(fname), form='unformatted')
END IF !write out daily files

!-----------------------------------------------------------------------------|
! Write out the header
! First get the grid centre point
!-----------------------------------------------------------------------------|
WRITE(*,*)'Generating C-CTM file header'
done=writeTAPM_header(oUnit(gse),.NOT.asciiYes,nems_ot,name_ems_ot,mpped_mw, &
                                               nglo,name_glo,mw_glo,gse_comment)
!
IF(asciiYes)THEN
  WRITE(oUnit(gse),100)nx_usr,ny_usr,dx_usr,dy_usr,x_center,y_center
100   FORMAT(i4,1x,i4,2(F10.3,1x),2(F15.3,1x))
ELSE
  WRITE(oUnit(gse))nx_usr,ny_usr,dx_usr,dy_usr,x_center,y_center
END IF

!-------------------------------------------------------------------------------
! Now build up the various species groups. This is done for each active cell,
!  for NOx, VOCs, PM, CO, SO2, NH3, mode number density, and miscellaneous
! Treat masked and un-masked data
!-------------------------------------------------------------------------------
WRITE(*,*)'Generating speciated emisssions data'
DO y=1,ny_usr
  DO x=1,nx_usr
   IF(spaf_usrM(x,y))THEN
    emsn(:,x,y)=0.0
    emsn_glo(:,x,y)=0.0

!-------------------------------------------------------------------------------
! Oxides of nitrogen (kg/day/cell)
!-------------------------------------------------------------------------------
    DO s=1,nNOx
      emsn(mapNOx(s),x,y)=spaf_usr(NOx_c,x,y)*NOx_splt(s,gse)*NOx_f
      !write(*,*)'temporarilly check values of mapnox',s,x,y, emsn(mapNOx(s),x,y)
    END DO

!-------------------------------------------------------------------------------
! VOCs - kg/day/cell
!-------------------------------------------------------------------------------
    DO s=1,nVOC
      emsn(mapVOC(s),x,y)=spaf_usr(VOC_c,x,y)*VOC_splt(s,gse)*VOC_f
      !write(*,*)'temporarilly check values of mapvoc',s,x,y, VOC_c,VOC_f,emsn(mapVOC(s),x,y)
    END DO

!-------------------------------------------------------------------------------
! PM (kg/day/cell)
!-------------------------------------------------------------------------------
    DO s=1,nPM
      emsn(mapPM(s),x,y)=spaf_usr(PM_c,x,y)*PM_splt(s,gse)*PM_f
    END DO

!-------------------------------------------------------------------------------
! Speciate OC into SOA precursors. Needs to happen after the PM is loaded
!-------------------------------------------------------------------------------
    DO s=1,nInv
      apa(s)=(emsn(loc25,x,y)+emsn(loc10,x,y))*vbs(s,gse)
      emsn(lapa+s-1,x,y)=apa(s)
    END DO
    DO s=nInv+1,nvbs
      apg(s)=(emsn(loc25,x,y)+emsn(loc10,x,y))*vbs(s,gse)
    END DO

!-------------------------------------------------------------------------------
! CO, SO2, NH3 (kg/day/cell)
!-------------------------------------------------------------------------------
    emsn(mapCO,x,y)=spaf_usr(CO_c,x,y)*CO_f
    emsn(mapSO2,x,y)=spaf_usr(SO2_c,x,y)*SO2_f
    emsn(mapNH3,x,y)=spaf_usr(NH3_c,x,y)*NH3_f

!-------------------------------------------------------------------------------
! Air toxics, tol, xyl, bnz, levo (kg/day/cell)
!-------------------------------------------------------------------------------
    DO s=1,nTOX
      emsn(mapTOX(s),x,y)=emsn(lVOC,x,y)*TOX_splt(s,gse)
    END DO

!-------------------------------------------------------------------------------
!  GLOMAP
! .. Calculate total particle volume (m^3 per cell per day)
! .. Calculate total particle number (per cell per day)
! .. Note 1x10^27 converts mode diameter^3 from nm^3 to m^3.
!   Sulfate
!-------------------------------------------------------------------------------
    DO l=1,n_su
      emsn_glo(l_su(m_su(l)),x,y)=f_su(l)*(emsn(lso4,x,y)+emsn(ls10,x,y)) !kg/cell/day
      modevol=emsn_glo(l_su(m_su(l)),x,y)/rhocomp(su_p)!*1.0E-03   !m^3/cell/day
      lgsd=LOG(gsig_su(l))
      emsn_glo(l_nd(m_su(l)),x,y)=1.0E27*modevol/((ppi/6.0)*(d_su(l)**3.0)*    &
                               EXP(4.5*lgsd*lgsd))+emsn_glo(l_nd(m_su(l)),x,y) !ptcl/cell/day
    END DO !sulfate

!-------------------------------------------------------------------------------
!   EC and OC (involatile and volatile) kg/cell/day
!   InSoluble Aitken mode; ptcl/cell/day
!-------------------------------------------------------------------------------
    DO l=1,n_ecoc
      emsn_glo(l_bc(m_ecoc(l)),x,y)=f_ecoc(l)*(emsn(lec25,x,y)+emsn(lec10,x,y))
      oc(m_ecoc(l))=0.0
 !
      DO v=1,nInv
        oc(m_ecoc(l))=oc(m_ecoc(l))+f_ecoc(l)*apa(v)
      END DO
      emsn_glo(l_oc(m_ecoc(l)),x,y)=oc(m_ecoc(l))
!
      modevol=(emsn_glo(l_bc(m_ecoc(l)),x,y)/rhocomp(bc_p)+    &
              emsn_glo(l_oc(m_ecoc(l)),x,y)/rhocomp(oc_p))!*1.0E-03
      lgsd=LOG(gsig_ecoc(l))
      emsn_glo(l_nd(m_ecoc(l)),x,y)=1.0E27*modevol/((ppi/6.0)*(d_ecoc(l)**3.0)*      &
                                    EXP(4.5*lgsd*lgsd))+emsn_glo(l_nd(m_ecoc(l)),x,y)
    END DO !ecoc

    DO s=nInv+1,nvbs
      emsn_glo(lapg+s-1,x,y)=apg(s)
    END DO

!-------------------------------------------------------------------------------
!   Other/Dust
!-------------------------------------------------------------------------------
    DO l=1,n_du
      emsn_glo(l_du(m_du(l)),x,y)=f_du(l)*(emsn(lot25,x,y)+emsn(lot10,x,y))
      modevol=emsn_glo(l_du(m_du(l)),x,y)/rhocomp(du_p)!*1.0E-03
      lgsd=LOG(gsig_du(l))
      emsn_glo(l_nd(m_du(l)),x,y)=1.0E27*modevol/((ppi/6.0)*(d_du(l)**3.0)*  &
                                  EXP(4.5*lgsd*lgsd))+emsn_glo(l_nd(m_du(l)),x,y)
    END DO  !dust
!
   ELSE
    emsn(:,x,y)=-1.0
    emsn_glo(:,x,y)=-1.0
   END IF !masked/un-masked
  END DO !x
END DO !y

!-----------------------------------------------------------------------------|
! Output some emission totals
!-----------------------------------------------------------------------------|
WRITE(*,*)'Domain Emission totals'
WRITE(*,*)'Total NOx (kg/day): ',qsum(emsn,mapNOx,spaf_usrM)
WRITE(*,*)'Total CO (kg/day) : ',SUM(emsn(mapCO,:,:),spaf_usrM)
WRITE(*,*)'Total SO2 (kg/day): ',SUM(emsn(mapSO2,:,:),spaf_usrM)
WRITE(*,*)'Total NH3 (kg/day): ',SUM(emsn(mapNH3,:,:),spaf_usrM)
WRITE(*,*)'Total VOC (kg/day): ',qsum(emsn,mapVOC,spaf_usrM)
WRITE(*,*)'Total PM (kg/day) : ',qsum(emsn,mapPM,spaf_usrM)
WRITE(*,*)'Total sulfate (kg/day): ',qsum1(emsn_glo,lsu1,lsu4,spaf_usrM)
WRITE(*,*)'Total ec (kg/day)     : ',SUM(emsn_glo(lbc5,:,:),spaf_usrM)
WRITE(*,*)'Total oc (kg/day)     : ',SUM(emsn_glo(lpo5,:,:),spaf_usrM)
WRITE(*,*)'Total dust (kg/day)   : ',qsum1(emsn_glo,ldu6,ldu7,spaf_usrM)
WRITE(*,*)'Total NUCL number (ptcl/day) : ',SUM(emsn_glo(lnucs,:,:),spaf_usrM)
WRITE(*,*)'Total AITS number (ptcl/day) : ',SUM(emsn_glo(laits,:,:),spaf_usrM)
WRITE(*,*)'Total ACCS number (ptcl/day) : ',SUM(emsn_glo(laccs,:,:),spaf_usrM)
WRITE(*,*)'Total COAS number (ptcl/day) : ',SUM(emsn_glo(lcoas,:,:),spaf_usrM)
WRITE(*,*)'Total AITI number (ptcl/day) : ',SUM(emsn_glo(laiti,:,:),spaf_usrM)
WRITE(*,*)'Total ACCI number (ptcl/day) : ',SUM(emsn_glo(lacci,:,:),spaf_usrM)
WRITE(*,*)'Total COAI number (ptcl/day) : ',SUM(emsn_glo(lcoai,:,:),spaf_usrM)

!-----------------------------------------------------------------------------|
! Write out a single day file in model time (UTC). Temporal profile is in LST.
! Calculate difference between model time and LST based on longitude
! Map from the internal emissions table to the user defined emissions table
! Also check for data masking before the conversions
!-----------------------------------------------------------------------------|
WRITE(*,*)'Writing data to C-CTM .gse file: ',TRIM(fname)
DO t=0,23
  IF(asciiYes)THEN
    DO y=1,ny_usr
      DO x=1,nx_usr
        h=MOD(24+t+INT(lon_usr(x)/15.),24)
        IF(spaf_usrM(x,y))THEN
          WRITE(oUnit(gse),2,ERR=90)(emsn(map_ems(k),x,y)*temporal(h,gse)*kgPhrTogPsec,k=1,nems_ot),    &
                                   (emsn_glo(k,x,y)*temporal(h,gse)*kgPhrTogPsec,k=1,l_nd(1)-1),       &
                                   (emsn_glo(k,x,y)*temporal(h,gse)*hrTosec,k=l_nd(1),l_nd(modes)) !no kg->g conversion for number density
        ELSE
         WRITE(oUnit(gse),2,ERR=90)(emsn(map_ems(k),x,y),k=1,nems_ot),    &
                                   (emsn_glo(k,x,y),k=1,l_nd(1)-1),       &
                                   (emsn_glo(k,x,y),k=l_nd(1),l_nd(modes)) !no kg->g conversion for number density
        END IF !masking
2       FORMAT(8(e10.3,1x))
      END DO !x
    END DO !y
  ELSE
    DO y=1,ny_usr
      DO x=1,nx_usr
        h=MOD(24+t+INT(lon_usr(x)/15.),24)
        IF(spaf_usrM(x,y))THEN
          WRITE(oUnit(gse),ERR=90)(emsn(map_ems(k),x,y)*temporal(h,gse)*kgPhrTogPsec,k=1,nems_ot),    &
                                  (emsn_glo(k,x,y)*temporal(h,gse)*kgPhrTogPsec,k=1,l_nd(1)-1),          &
                                  (emsn_glo(k,x,y)*temporal(h,gse)*hrTosec,k=l_nd(1),l_nd(modes)) !no kg->g conversion for number density
        ELSE
          WRITE(oUnit(gse),ERR=90)(emsn(map_ems(k),x,y),k=1,nems_ot),    &
                                  (emsn_glo(k,x,y),k=1,l_nd(1)-1),       &
                                  (emsn_glo(k,x,y),k=l_nd(1),l_nd(modes)) !no kg->g conversion for number density
        END IF ! masking
      END DO !x
    END DO  !y
  END IF  !ascii?
END DO !hour loop

!-----------------------------------------------------------------------------|
! Finished
!-----------------------------------------------------------------------------|
CLOSE(oUnit(gse))
CLOSE(sUnit)
DEALLOCATE(m_ecoc)
DEALLOCATE(d_ecoc)
DEALLOCATE(gsig_ecoc)
DEALLOCATE(f_ecoc)
!
DEALLOCATE(m_su)
DEALLOCATE(d_su)
DEALLOCATE(gsig_su)
DEALLOCATE(f_su)
!
DEALLOCATE(m_du)
DEALLOCATE(d_du)
DEALLOCATE(gsig_du)
DEALLOCATE(f_du)
!
DEALLOCATE(emsn)
DEALLOCATe(hames)
DEALLOCATE(spaf_usr)
DEALLOCATE(spaf_usrM)
DEALLOCATE(lat_usr)
DEALLOCATE(lon_usr)
DEALLOCATE(spaf_data)
STOP 'Sucessful completion'
90 PRINT *,'Error writing to the file: ',TRIM(fname)
END PROGRAM spaemis_glo
