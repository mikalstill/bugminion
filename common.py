import datetime
import subprocess


SAVED_FIELDS = ['id', 'date_created', 'date_last_updated', 'description',
                'information_type', 'tags', 'title', 'web_link']
SAVED_TASK_FIELDS = ['assignee_link', 'date_assigned', 'importance', 'status']

DISPLAY_ORDER = ['id', 'title', 'importance', 'status', 'date_created']

PRIORITIES = ['Critical', 'High', 'Medium', 'Low', 'Wishlist', 'Undecided',
              'Unknown']

QUESTIONS = ['rationale',
             'importance (1 to 5, 5 being high)',
             'skills (space separated tags)']


def clobber_object(container, name, data):
    try:
        container.delete_object(name)
    except:
        pass
    container.store_object(name, data)


def get_most_recent_dump(container, project):
    dump_files = []
    for dump_file in container.get_objects(prefix='%s/' % project):
        dump_files.append(dump_file.name)
    return sorted(dump_files)[-1]


def triages(container, project, bug):
    return sorted(container.get_objects(
        prefix='%s-bug/%s-' %(project, bug)))


def recently_triaged(triages):
    # Have we triaged this one in the last 30 days?
    if triages:
        most_recent_triage = \
            triages[-1].name.split('/')[-1].split('-')[-1]
        most_recent_datetime = datetime.datetime(
            int(most_recent_triage[0:4]),
            int(most_recent_triage[4:6]),
            int(most_recent_triage[6:8]))
        age = datetime.datetime.now() - most_recent_datetime
        return age.days < 30

    return False


def runcmd(cmd):
    obj = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, shell=True)
    (stdout, stderr) = obj.communicate()
    returncode = obj.returncode
    return stdout
