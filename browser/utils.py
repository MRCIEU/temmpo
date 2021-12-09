from datetime import datetime, timedelta
import logging

from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from browser.models import SearchResult, Upload, SearchCriteria
from django.core.mail import send_mail
from django.template import loader, Context

logger = logging.getLogger(__name__)


def remove_incompleted_registrations():
    # Delete incomplete users account, where user never triggered email activation of their account within the given ACCOUNT_ACTIVATION_DAYS currently 14 days as per registration email
    past_date_delete = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
    incomplete_users = User.objects.exclude(is_active=True).exclude(is_superuser=True).exclude(date_joined__gt=past_date_delete)
    results = incomplete_users.delete()
    logger.info("Status of registration and user deletions")
    logger.info(results)


def user_clean_up(no_deletion=False, warn_historic=False):
    """
    Automated clean up of users and associated searches
    Tom requested that users be deleted if they have been inactive for a year.
    They should receive an email warning two months before deletion.
    We only warn uses that have activated accounts, others are just deleted.
    We don't delete super-users.

    As this hasn't been run and the site has been live for some time we
    need to account for the fact that some users would be deleted immediately.
    To deal with this we have flags preventing deletion.

    no_deletion = warn users but do not delete
    warn_historic = flag for handling initial run of script

    The script is intended to be run DAILY.
    """

    past_date_delete = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=365)
    past_date_warn_min = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=settings.ACCOUNT_CLOSURE_WARNING)
    past_date_warn_max = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=(settings.ACCOUNT_CLOSURE_WARNING + 1))

    # Delete inactive users after a year
    if not no_deletion and not warn_historic:
        # Incomplete users did not activate their account
        incomplete_users = User.objects.exclude(is_active=True).exclude(is_superuser=True)\
            .exclude(date_joined__gt=past_date_delete)
        for incomplete_user in incomplete_users:
            # Looping separately rather than using .delete() on queryset to make sure custom delete function is used
            delete_user_content(user_id=incomplete_user.id)
            incomplete_user.delete()

        # Delete users that haven't logged in for a year
        inactive_users = User.objects.filter(is_active=True).exclude(is_superuser=True)\
            .exclude(last_login__gt=past_date_delete)
        for inactive_user in inactive_users:
            # Looping separately rather than using .delete() on queryset to make sure custom delete function is used
            delete_user_content(user_id=inactive_user.id)
            inactive_user.delete()

    # Warn users about impending deletion
    if warn_historic:
        # Deal with historic warnings - because clean up only being done after site has been live for some time
        # This is basically a RUN ONCE flag when enabling this for the first time
        users_to_warn = User.objects.filter(is_active=True).exclude(is_superuser=True)\
            .exclude(last_login__gt=past_date_warn_min)
    else:
        # Normal running of utility is to warn people if they have been inactive for 10 months
        # Script should run daily and some we just need to know who last logged in ten months ago, to the day
        # If this script doesn't run for some reason then users may not get alerted but they won't have used the site
        # for a year before being deleted and that seems reasonable.
        users_to_warn = User.objects.filter(is_active=True).exclude(is_superuser=True)\
            .exclude(last_login__gt=past_date_warn_min).exclude(last_login__lt=past_date_warn_max)

    # Send warning
    for user_to_warn in users_to_warn:
        send_closure_warning(user_to_warn)


def delete_user_content(user_id):
    """
    Special function to allow us to delete all the related database and uploaded files associated with a specific user
    """
    all_user_searches = SearchResult.objects.filter(criteria__upload__user=user_id)

    # Delete searches
    for user_search in all_user_searches:
        user_search.delete()

    all_user_search_criteria = SearchCriteria.objects.filter(upload__user=user_id)

    # Delete search criteria
    for user_search_criteria in all_user_search_criteria:
        user_search_criteria.delete()

    # Check for remaining uploads
    remaining_uploads = Upload.objects.filter(user=user_id)
    for left_upload in remaining_uploads:
        left_upload.delete()


def send_closure_warning(user_account):
    """
    Send closure warning emails to users that haven't accessed TeMMPo for 10 months.
    """
    subject = loader.get_template('account/closure_warning_email_subject.txt').render({})
    message = loader.get_template('account/closure_warning_email.txt').render({})
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_account.email, ])
    logger.info('User: %s warned about account closure' % user_account.id)

