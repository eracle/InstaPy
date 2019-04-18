import random
import time

from selenium.common.exceptions import NoSuchElementException

from instapy.unfollow_util import scroll_to_bottom_of_followers_list, get_buttons_from_dialog, \
    dialog_username_extractor, follow_through_dialog
from .time_util import sleep
from .util import click_element
from .util import get_relationship_counts
from .util import is_page_available
from .util import progress_tracker
from .util import scroll_bottom
from .util import web_address_navigator


def delta_followers(session, user_name, max_amount=100, past_followers=None):
    """
    Given an instagram username and an optional list of past_followers, retrieves the list of new followers.
    :param session:
    :param user_name:
    :param max_amount:
    :param old_followers:
    :return:
    """
    if past_followers is None:
        past_followers = []

    session.quotient_breach = False

    try:

        user_name = user_name.strip()

        user_link = "https://www.instagram.com/{}/".format(user_name)
        web_address_navigator(session.browser, user_link)

        if not is_page_available(browser=session.browser,
                                 logger=session.logger):
            return []

        # check how many people are following this user.
        allfollowers, allfollowing = get_relationship_counts(browser=session.browser,
                                                             username=user_name,
                                                             logger=session.logger)

        # skip early for no followers
        if not allfollowers:
            session.logger.info("'{}' has no followers".format(user_name))
            return []

        elif allfollowers < max_amount:
            session.logger.warning("'{}' has less followers- {}, than the given amount of {}".format(
                    user_name, allfollowers, max_amount))

        # locate element to user's followers
        try:
            followers_link = session.browser.find_elements_by_xpath(
                '//a[@href="/{}/followers/"]'.format(user_name))
            if len(followers_link) > 0:
                click_element(session.browser, followers_link[0])
            else:
                session.logger.error("'{} is private'".format(user_name))
                return []
        except NoSuchElementException:
            session.logger.error(
                'Could not find followers\' link for {}'.format(user_name))
            return []

        except BaseException as e:
            session.logger.error("`followers_link` error {}".format(str(e)))
            return []

        channel = "Follow"
        wait_seconds = 10

        sleep(1)

        if max_amount > int(allfollowers * 0.85):
            # taking 85 percent of possible amounts is
            # a safe study
            max_amount = int(allfollowers * 0.85)
        try_again = 0
        sc_rolled = 0

        # find dialog box
        # change made wrt Instapy master branch:
        # in order to get the following method more robust to possible changes on the html
        # I am getting all the bottom dialog webelements, and I am taking the first
        dialog_address = "//body/div/div/div[2]"
        dialog = session.browser.find_elements_by_xpath(dialog_address)[0]

        # scroll to end of follower list to initiate first load which hides the
        # suggestions
        scroll_to_bottom_of_followers_list(session.browser, dialog)

        buttons = get_buttons_from_dialog(dialog, channel)

        abort = False
        total_list = len(buttons)
        simulator_counter = 0
        start_time = time.time()

        # scroll down if the generated list of user to follow is not enough to
        # follow amount set
        while (total_list < max_amount) and not abort:
            before_scroll = total_list
            for i in range(4):
                scroll_bottom(session.browser, dialog, 2)
                sc_rolled += 1
                simulator_counter += 1
                buttons = get_buttons_from_dialog(dialog, channel)

                # breaking the scroll if past follower is encountered
                partial_usernames_extracted = dialog_username_extractor(buttons)
                for person in partial_usernames_extracted:
                    if person in past_followers:
                        abort = True

                total_list = len(buttons)
                progress_tracker(total_list, max_amount, start_time, session.logger)

            if not abort:
                abort = (before_scroll == total_list)

            if abort:
                if total_list < max_amount:
                    session.logger.info("Failed to load desired amount of users!\n")

            if sc_rolled > 85:  # you may want to use up to 100
                if total_list < max_amount:
                    # print('')
                    session.logger.info(
                        "Too many requests sent!  attempt: {}  |  gathered "
                        "links: {}"
                        "\t~sleeping a bit".format(try_again + 1, total_list))
                    sleep(random.randint(wait_seconds, int(wait_seconds * 1.09)))
                    try_again += 1
                    sc_rolled = 0

        print('')
        usernames_xpath = "//*/div/div/a[@href and @title]"
        usernames_elements = session.browser.find_elements_by_xpath(usernames_xpath)

        person_list = [elem.text for elem in usernames_elements]

    except (TypeError, RuntimeWarning) as err:
        session.logger.error(
            'Sorry, an error occurred: {}'.format(err))
        session.aborting = True
        return []

    return person_list
