#/usr/bin/env python
import commands
import os
from subprocess import call

finished_cells =[]

def write_file(filename, contents):
   """Write the given contents to a text file.

   ARGUMENTS
       filename (string) - name of the file to write to, creating if it doesn't exist
       contents (string) - contents of the file to be written
   """

   # Open the file for writing
   file = open(filename, 'w')

   # Write the file contents
   file.write(contents)

   # Close the file
   file.close()

   return

def qsub_submit(command_filename, hold_jobid = None, name = None):
  """Submit the given command filename to the queue.

  ARGUMENTS
      command_filename (string) - the name of the command file to submit

  OPTIONAL ARGUMENTS
      hold_jobid (int) - job id to hold on as a prerequisite for execution

  RETURNS
      jobid (integer) - the jobid
  """

  # Form command
  command = 'qsub'
  if name: command += ' -N %s' % name
  if hold_jobid: command += ' -hold_jid %d' % hold_jobid
  command += ' %s' % command_filename

  # Submit the job and capture output.
  import subprocess
  print "> " + command
  process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
  out, err = process.communicate()
  print(out)

  # Match job id
  jobid = out.split(' ')[2]

  return int(jobid)

path = '/netapp/home/idriver/01272015'
out= '${TMPDIR}'
annotation_file = '/netapp/home/idriver/mm10_ERCC/genes/genes.gtf'
index_gen_loc = '/netapp/home/idriver/mm10_ERCC/Bowtie2Index_mm10/mm10_ERCC'

pathlist = []
for root, dirs, files in os.walk(path):
  if 'fastq' in root:
    pathlist.append([root,files])
for p in pathlist:
  n = p[0].strip('/').split('/')
  namef = n[-1].split('_')[0]
  data_file = p[0]
  result_file = os.path.join(out,namef)
  input_files=''
  r_num = []
  for f in p[1]:
    if 'fastq' in f:
      f_split = f.split('_')
      r_name = (f_split[3][1])
      en_split = f_split[4].split('.')
      p_num = en_split[0].strip('00')
      rank = r_name+p_num
      r_num.append(int(rank))
      input_files+=os.path.join(p[0],f)+' '
  in_split = input_files.split(' ')
  sort_num = [x for (y,x) in sorted(zip(r_num,in_split))]
  if len(in_split) > 2:
    name_build = ''
    for i, mul_f in enumerate(sort_num):
      if 'fastq' in mul_f:
        if i == len(in_split)-1:
          name_build+=mul_f
        elif i < (len(in_split)/2)-1 or i > (len(in_split)/2)-1:
          name_build+= mul_f+','
        elif i ==  (len(in_split)/2)-1:
          name_build+= mul_f+' '
    final_files = name_build.strip(',')
  elif len(in_split) == 2:
    final_files = sort_num[0]+' '+sort_num[1].strip(',')
  tophat_cmd = 'tophat2 -p 8 -r 50 -G '+annotation_file+' --transcriptome-index=/netapp/home/idriver/transcriptome_data_mm10/known -o '+result_file+' '+index_gen_loc+' '+final_files
  samtools_cmd = 'samtools sort '+result_file+'/'+'accepted_hits.bam accepted_hits_sorted'
  cufflinks_cmd = 'cufflinks -p 8 -G '+annotation_file+' -o '+result_file+' '+result_file+'/'+'accepted_hits.bam'
  cuffquant_cmd = 'cuffquant -p 8 -o '+result_file+' '+annotation_file+' '+result_file+'/'+'accepted_hits.bam'
  # Write script.
  contents = """\
#!/bin/sh
#$ -l arch=linux-x64
#$ -S /bin/bash
#$ -o /netapp/home/idriver/results_cindy_rna
#$ -e /netapp/home/idriver/error_spc
#$ -cwd
#$ -r y
#$ -j y
#$ -l netapp=20G,scratch=80G,mem_total=24G
#$ -pe smp 8
#$ -R yes
#$ -l h_rt=9:59:00

set echo on

date
hostname
pwd

export PATH=$PATH:${HOME}/bin
PATH=$PATH:/netapp/home/idriver/cufflinks-2.2.1.Linux_x86_64
PATH=$PATH:/netapp/home/idriver/bin/bowtie2-2.2.3
PATH=$PATH:/netapp/home/idriver/bin/samtools-0.1.19_2
PATH=$PATH:/netapp/home/idriver/bin/tophat-2.0.13.Linux_x86_64
PATH=$PATH:/usr/bin/gunzip
export PATH
echo $PATH
export TMPDIR=/scratch
echo $TMPDIR
cd $TMPDIR
mkdir %(namef)s
mkdir -p /netapp/home/idriver/results_cindy_rna/%(namef)s

%(tophat_cmd)s
%(cufflinks_cmd)s
%(cuffquant_cmd)s

# Copy the results back to the project directory:
cd $TMPDIR
cp -r %(namef)s/* /netapp/home/idriver/results_cindy_rna/%(namef)s
rm -r %(namef)s

date
  """ % vars()
  if namef == 'D7-E3' or namef == 'D7-E2' :
    filename = '%s_cindy.sh' % namef
    write_file(filename, contents)
    print tophat_cmd
    print cufflinks_cmd
    print cuffquant_cmd
    jobid = qsub_submit(filename, name = '%s_cindy' % namef)
    print "Submitted. jobid = %d" % jobid
    # Write jobid to a file.
    import subprocess
    process = subprocess.Popen('echo %d > jobids' % jobid, stdout=subprocess.PIPE, shell = True)
    out, err = process.communicate()
    print(out)
