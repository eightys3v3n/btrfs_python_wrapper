import subprocess
import time
import os
import re


date_format = '%Y_%m_%d_%H_%M_%S'


class BTRFSError(Exception):
  pass


class CreateSnapshotError(Exception):
  pass


class DeleteSnapshotError(Exception):
  pass


def subvolumes(path=None):
  """
  Returns a list of subvolumes in the given path.
  """
  p = subprocess.Popen(['btrfs', 'subvolume', 'list', '/'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  d = p.communicate()

  if p.returncode:
    raise BTRFSException(d[1].decode())

  volumes = d[0].decode()
  volumes = volumes.split('\n')
  volumes = volumes[0:-1]

  for i,v in enumerate(volumes):
    volumes[i] = re.search('path .*', v).group()
    volumes[i] = volumes[i][5:]
    volumes[i] = '/'+volumes[i]

  if path is not None:
    _volumes = []
    for v in volumes:
      if v == path:
        continue
      elif v.startswith(path):
        _volumes.append(v)
    volumes = _volumes

  return volumes


def timestamp_subvolumes(path=None):
  """
  Returns a list of subvolumes and the timestamp represented in the name.
  ('/snapshots/2017_08_14_20_44_21', a time object that can be compared with >, <, ==)
  """
  volumes = subvolumes(path=path)
  _volumes = []
  for v in volumes:
    n = os.path.basename(v)
    try:
      timestamp = time.strptime(n, date_format)
    except ValueError:
      print("skipping invalid formatted snapshot '{}'".format(v))
      continue
    _volumes.append((v, timestamp))
  volumes = _volumes
  return volumes


def create_snapshot(src, dst):
  """
  Creates a snapshot of src at dst.
  """
  p = subprocess.Popen(['btrfs', 'subvolume', 'snapshot', src, dst], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  d = p.communicate()

  if p.returncode:
    raise BTRFSException(d[1].decode())

  res = re.match("Create a snapshot of '{}' in '/{}'\n".format(src,dst), d[0].decode())
  if res is None:
    raise CreateSnapshotError(d[0].decode())

  return False


def delete_snapshot(path):
  c = input("delete subvolume {}? ".format(path))
  if c.lower() not in ['yes', 'y']:
    return True

  p = subprocess.Popen(['btrfs', 'subvolume', 'delete', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  d = p.communicate()

  res = re.match("Delete subvolume.*: '/{}'\n".format(path), d[0].decode())
  if res is None:
    raise DeleteSnapshotError(d[0].decode())

  return False


def diffs(old, new):
  """
  Returns a list of modified files between the two snapshots.
  """
  old_id = subprocess.Popen(['btrfs', 'subvolume', 'find-new', old, '9999999'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read()
  old_id = re.search('[0-9]+', old_id.decode()).group()

  p = subprocess.Popen(['btrfs', 'subvolume', 'find-new', new, old_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  d = p.communicate()

  if p.returncode:
    raise BTRFSError(d[1])

  d = d[0].decode()
  diffs = d.split('\n')
  diffs = diffs[0:-2]

  diffs = [d[d.find('flags')+6:] for d in diffs]
  diffs = [d[d.find(' ')+1:] for d in diffs]

  return diffs


def timestamp_snapshot(src, dst):
  """
  Creates a snapshot of src into dst, named the current date & time.
  """
  timestamp = time.strftime(date_format)
  dst = os.path.join(dst, timestamp)
  return create_snapshot(src, dst)


def test():
  print("no tests yet")


if __name__ == '__main__':
  timestamp_snapshot('/data', '/')