#!/bin/bash
# script to build vpx,vgx,vlx,vpv,gse, and whe emissions using the Victoria 2016 inventory
# srv csiro 15/2/2021
# Modifications
#-------------------------------------------------------------------------------------------
# who   when    what
# srv 15/02/21  preliminary version 0.1
# srv 15/02/21  setup bash script for each emission source and link to nsw species mappings
# srv 15/05/21  revised to map species to GMR 2013; tidy-up steps applied; all gse sources merged and naming conventions applied
#

#module load python/3.6.1

#-------------------------------------------------------------------------------------------
# set up scenarios and options
#-------------------------------------------------------------------------------------------
yyyy=$1
mm=$2
mm_name=$3
dd=$4
offset=$5
datapath=$6
de=$dd

#-------------------------------------------------------------------------------------------
# testing
#-------------------------------------------------------------------------------------------
#yyyy=2015
#mm=06
#mm_name=jun15
#dd=01
#set de=01
#offset=-8
#datapath=/datasets/work/oa-nrde/work/emissions/anthropogenic/wa2/2012/datafiles
#de=$dd

#excdir=/scratch1/van485/test_pth
# set up links to software executables
exepath=..
spaemis_exe=..

srcList=(aircraft rail shipping motor_vehicles crematoria petcrematoria industry_diffuse architect_coating bakery charcoal cutback_bitumen domestic_solvents dry_cleaning gas_leak panel_beaters printing servos pizza vicbakery woodheater)
#srcList=(vpx vdx vlx vpv non-exh-pm)

num_src=${#srcList[@]}
#num_src=27
#echo $num_src

echo $exepath
#generate all the .run files for all emissions sources
python $exepath/gse_emis.py $yyyy $mm $dd $datapath

# now for each source lets generate the emissions by running spaemis
src=0
while [ $src -lt $num_src ]; do

  echo "Running spaemis_glo for ${srcList[src]}"
  cp ${srcList[src]}.run spaemis_glo.run
  ${spaemis_exe}/spaemis_glo >& ${srcList[src]}.trace

#cat <<eof >gse_check.run
#  Output emission totals and spatial plot for a .gse
#  CTM fileName of file to be checked
#  ${srcList[src]}.in.gse.bin
#  Number of days to process
#  1
#  Species name for spatial plotting
#  CO
#eof
#  ${gse_check_exe}/gse_check >&gse_check.trace
#  mkdir -p  ${srcList[src]}
#  mv gse_totals.csv  ${srcList[src]}/
#  mv gse_check.trace ${srcList[src]}/
#  mv *CO_kgPerDay* ${srcList[src]}/

  let src=$((src + 1))

done
#merge all gse sources except wood heaters
# note that this file does not include wood heater emissions
cat <<eof >gsemergem.run
Run file for the multi-file version of psemerge(m)
Output file name .gse (ascii); .gse.bin (binary)
${yyyy}_${mm_name}_vic.gse.bin
Number of output days (note input files with < ndays will cycle from day 1)
1
List of input files (enclosed in the keywords "startfilelist" "endfilelist")
startfilelist
aircraft.in.gse.bin
rail.in.gse.bin
shipping.in.gse.bin
motor_vehicles.in.gse.bin
crematoria.in.gse.bin
petcrematoria.in.gse.bin
industry_diffuse.in.gse.bin
architect_coating.in.gse.bin
bakery.in.gse.bin
charcoal.in.gse.bin
cutback_bitumen.in.gse.bin
domestic_solvents.in.gse.bin
dry_cleaning.in.gse.bin
gas_leak.in.gse.bin
panel_beaters.in.gse.bin
printing.in.gse.bin
servos.in.gse.bin
pizza.in.gse.bin
vicbakery.in.gse.bin
endfilelist
Optionally mask out data in the first input file (keyword "maskingfile")
nomaskingfile
eof

# ${gsemerge_exe}/gsemergem >&gsemergem_vic.trace

# now do the wood heater emissions
#cat <<eof >gsemergem.run
#Run file for the multi-file version of psemerge(m)
#Output file name .gse (ascii); .gse.bin (binary)
#${yyyy}_${mm_name}_vic_whe.bin
#Number of output days (note input files with < ndays will cycle from day 1)
#1
#List of input files (enclosed in the keywords "startfilelist" "endfilelist")
#startfilelist
#woodheater.in.gse.bin
#endfilelist
#Optionally mask out data in the first input file (keyword "maskingfile")
#nomaskingfile
#eof

#${gsemerge_exe}/gsemergem >&gsemergem_vic_whe.trace

mv woodheater.in.gse.bin ${yyyy}_${mm_name}_vic_whe.bin

# cleanup
#tarfile="/datastore/ute002/emissions/epa_vic_gse/archive/${yyyy}_${mm_name}_${dd}_vic-3km_dynamic.tar"
#tar -czvf $tarfile *.trace *.run
#rm *.in.*bin
#rm *.trace
#rm woodheater.in.gse.bin
#rm aircraft.in.gse.bin rail.in.gse.bin shipping.in.gse.bin motor_vehicles.in.gse.bin crematoria.in.gse.bin petcrematoria.in.gse.bin industry_diffuse.in.gse.bin architect_coating.in.gse.bin bakery.in.gse.bin charcoal.in.gse.bin cutback_bitumen.in.gse.bin domestic_solvents.in.gse.bin dry_cleaning.in.gse.bin gas_leak.in.gse.bin panel_beaters.in.gse.bin printing.in.gse.bin servos.in.gse.bin pizza.in.gse.bin vicbakery.in.gse.bin
#rm *.trace *.run *.grd
#rm aircraft.trace rail.trace shipping.trace motor_vehicles.trace crematoria.trace petcrematoria.trace industry_diffuse.trace architect_coating.trace bakery.trace charcoal.trace cutback_bitumen.trace domestic_solvents.trace dry_cleaning.trace gas_leak.trace panel_beaters.trace printing.trace servos.trace pizza.trace vicbakery.trace
