#!usr/bin/env python
#encoding: utf-8
__author__="luzhijun"
'''
upload_download test
'''
from externals.simple_oss import SimpleOss
import os,tarfile,logging,time
from batchcompute import (
    Client, JobDescription, TaskDag, TaskDescription, ResourceDescription,ClientError
)
import config as cfg
oss_clnt = SimpleOss(cfg.OSS_HOST, cfg.ID, cfg.KEY)



def get_job_desc():
    job_desc = JobDescription()
    task = TaskDescription()
    resource = ResourceDescription()

    resource.Cpu = cfg.CPU_NUM*100
    resource.Memory = 16000
    # Create task.
    task.ResourceDescription = resource
    task.PackageUri = cfg.FULL_PACKAGE
    task.ProgramName = 'end.py'
    task.ProgramType = 'python'
    task.ImageId = cfg.IMAGE_ID
    #task.InstanceCount = cfg.COUNT_TASK_NUM
    task.InstanceCount = cfg.INSTANCE_NUM
    task.EnvironmentVariables = {}
    task.StdoutRedirectPath = cfg.LOG_PATH
    task.StderrRedirectPath = cfg.LOG_PATH
    task.OssMapping={cfg.FULL_DATAPATH:cfg.LOCAL_DATA}
    task.OssMappingLock=cfg.LOCK
    task.OssMappingLocale=cfg.LOCALE
    # Create task dag.
    task_dag = TaskDag()
    task_dag.add_task(task_name='download', task=task)
    job_desc.TaskDag = task_dag
    job_desc.JobName = 'dtest'
    job_desc.Priority = 1000
    return job_desc


def tar_upload(bucket, local_dir, oss_path):
    '''
    A function to help upload worker package to oss.
    '''
    local_tarfile = 'udtest.tar.gz'
    if os.path.exists(local_tarfile): os.remove(local_tarfile)

    def do_tar(worker_dir, tar_file):
        '''
        A function to tar worker package.
        '''
        tar = tarfile.open(tar_file, 'w:gz')
        cwd = os.getcwd()
        os.chdir(worker_dir)
        for root,dir,files in os.walk('.'):
            for file in files:
                tar.add(os.path.join(root, file))
        os.chdir(cwd)
        tar.close()

    do_tar(local_dir, local_tarfile)
    oss_clnt.upload(bucket, local_tarfile, oss_path)

def listenRes():
    t=time.time()
    while time.time()-t>60:
        oss_clnt.list(cfg.OSS_BUCKET,"test/data/")
        time.sleep(0.02)

def main():
    tar_upload(cfg.OSS_BUCKET, 'worker_package', cfg.PACKAGE_PATH)
    batch_clnt = Client(cfg.REGION, cfg.ID, cfg.KEY)
    job=batch_clnt.create_job(get_job_desc())
    if not oss_clnt.exists(cfg.OSS_BUCKET,cfg.REQUEST_NAME):
        oss_clnt.upload_str(cfg.OSS_BUCKET,"This is a test!",cfg.REQUEST_NAME)
    t = 10
    print 'Sleep %s second, please wait.'%t
    time.sleep(t)
    try:
    	while(True):
            jobId=job.JobId
            job_detail = batch_clnt.get_job(jobId)
            if job_detail.State in ['Waiting', 'Running']:
                print('Job %s is now %s'%(job, job_detail.State))
                time.sleep(10)
                listenRes()
                continue
            else:
                # 'Failed', 'Stopped', 'Finished'
            	print('Job %s is now %s'%(job, job_detail.State))
            	if job_detail.State == 'Finished':
            	    #oss_clnt.download(cfg.OSS_BUCKET,'/Users/trucy/luzj/test_ud/awq1.txt',cfg.RESPONSE_NAME)
            	    print('Finished')
            	break
    except ClientError, e:
        print(e)  

if __name__ == '__main__':     
    main()


    











