SAVED_FIELDS = ['id', 'date_created', 'date_last_updated', 'description',
                'information_type', 'tags', 'title', 'web_link']
SAVED_TASK_FIELDS = ['assignee_link', 'date_assigned', 'importance', 'status']

DISPLAY_ORDER = ['id', 'title', 'importance', 'status', 'date_created']

QUESTIONS = ['importance (1 to 5, 5 being high)',
             'skills (space separated tags)']


def clobber_object(container, name, data):
    try:
        container.delete_object(name)
    except:
        pass
    container.store_object(name, data)
