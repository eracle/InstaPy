from selenium.common.exceptions import NoSuchElementException

from instapy.unfollow_util import get_users_through_dialog
from instapy.util import web_address_navigator, is_page_available, get_relationship_counts, click_element


def delta_followers(session, user_name, max_amount, past_followers=None):
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
        # print(allfollowers)
        # print(allfollowing)

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

        person_list, _ = get_users_through_dialog(browser=session.browser,
                                                  login=session.username,
                                                  user_name=user_name,
                                                  amount=max_amount,
                                                  users_count=allfollowers,
                                                  randomize=False,
                                                  dont_include=[],
                                                  blacklist=session.blacklist,
                                                  follow_times=session.follow_times,
                                                  simulation={"enabled": False, "percentage": 100},
                                                  channel="Follow",
                                                  jumps=session.jumps,
                                                  logger=session.logger,
                                                  logfolder=session.logfolder,
                                                  past_followers=past_followers,
                                                  wait_seconds=10,
                                                  )

    except (TypeError, RuntimeWarning) as err:
        session.logger.error(
            'Sorry, an error occurred: {}'.format(err))
        session.aborting = True
        return []

    return person_list
