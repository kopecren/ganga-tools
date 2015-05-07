import Ganga
import GangaDirac
from Ganga.GPIDev.Base.Proxy import GPIProxyObject
from Ganga.GPIDev.Lib.Job.Job import Job
from Ganga.GPIDev.Lib.File.IGangaFile import IGangaFile


def subjobs(jobs):
    """Return an interator on the (flattened) subjobs."""
    if isinstance(jobs, GPIProxyObject) and isinstance(jobs._impl, Job):
        if len(jobs.subjobs):
            for j in jobs.subjobs: yield j
        else:
            yield jobs
    else:
        for job in jobs:
            for j in subjobs(job):
                yield j


def is_existing_file(file):
    """Is a an existing physical file is represented by a Ganga file object?"""

    if not isinstance(file, GPIProxyObject) or not isinstance(file._impl, IGangaFile):
        raise ValueError('file must be a Ganga file object!')

    if isinstance(file._impl, GangaDirac.Lib.Files.DiracFile):
        ok = bool(file.lfn)
    elif isinstance(file, Ganga.GPIDev.Lib.File.MassStorageFile):
        ok = bool(file.location())
    else:
        raise NotImplementedError('Do not know how to check if file exits {}'.format(repr(file)))

    return ok


def outputfiles(jobs, pattern, one_per_job=False, ignore_missing=False):
    """Return a flat list of outputfiles matching the pattern for the given jobs."""
    files = []
    for job in subjobs(jobs):
        job_files = job.outputfiles.get(pattern)
        if one_per_job:
            if len(job_files) == 0:
                raise RuntimeError('File "{}" not found in job {}'.format(pattern, job.fqid))
            elif len(job_files) > 1:
                raise RuntimeError('Too many files matching pattern "{}" for job {}'.format(pattern, job.fqid))
        for file in job_files:
            # Here we need to check that the file exists. Unfortunatelly, Ganga does
            # not provide an abstract method of IGangaFile to do that, hence the "hack".
            if not is_existing_file(file):
                msg = 'File {} from job {} does not represent an existing physical file!'.format(repr(file), job.fqid)
                if not ignore_missing:
                    raise RuntimeError(msg + '\nAre all (sub)jobs completed?')
                else:
                    print 'WARNING:', msg, 'Will ignore it!'
            else:
                files.append((job, file))
    return files