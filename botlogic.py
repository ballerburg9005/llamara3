from getpass import getpass
import threading
from argparse import ArgumentParser
import subprocess
import tempfile
import os
import requests
import logging
import asyncio
import aiohttp
import json
import mimetypes
import pathlib
import random
import string
import re
import sys
import imghdr
from datetime import datetime, time, timedelta, timezone
from aiohttp import ClientSession, ClientTimeout
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pytz

import sqlite3


class BotLogic():
    def __init__(self):

        self.api_url = 'http://localhost:11434/api/chat'
        self.headers = {
            "Host": "localhost:11434",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "Python/3.11 aiohttp/3.9.5",
            "Content-Type": "text/plain; charset=utf-8"
        }

        # TTS API configuration
        self.tts_api_url = 'http://localhost:8000/v1/audio/speech'
        self.tts_headers = {
            "Authorization": "Bearer sk-111111111",  # Replace with your actual token
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Connection": "keep-alive"
        }

        self.randphone = random.randint(0, 30)
        self.mood_swing = ""
        self.mood_swing_since = 0
        self.mood_swing_modded_user_query = 0

        self.avatar_is_uploaded = False

        self.model = "llama3.1:8b-text-fp16"
        self.description = "Llamara3: Personal assistant, project and schedule manager, coach, motivator, angry girlfriend and salvation."

        self.settable_userfields = {"info", "project", "schedule", "important", "worktime", "mealtime", "relaxtime", "commute", "meal", "timezone", "google_calendar_email", "google_service_account_json_key", "name"}


        # if the description is empty, the AI don't has to write #punishment_successful to exit the mode

        # new punishment ideas:
            #audit    - pretends writing a report on user to use against him
            #retarded - treats user as if he has IQ of 70 and is handicapped
            #baby     - treats user as if he is 5 years old
        
            #meltdown - "can't take your bullshit anymore" argument
            


        # type: punishment, one-shot, 

        # execute    : user has to execute behavior
        # threat     : user has beg repeatedly to avert consequence
        # apology    : user has to apologize
        # affirm     : user has to affirm something as true elborately
        # one-shot   : hashtag modifies something internal , e.g. ignore X minutes
        # timeout    : ends after fixed time
        # modtoday   : ruins e.g. mood for entire day
        # punishment : it is a punishment

        # uitmatum : user has to do task within x minutes or else spent e.g. bitcoin

        # ??? belittle, distant, mothering, philosopher, victim, condescending, toxicoptimism, insecure, teasing, judgemental, blackmail, jealous, sarcastic, 
        # ???? cryptic, apologetic, indifferent, overly-formal (business), evasive, distrust, cheesy, intellectualizing, impatient, melodramatic, dismissive, parental, 
        # defensive,
        # innuendo, hyper-emotional, pessimistic, mocking, revenge, bored, smothering, stoic, confused, competitive, distracted, secretive, theatrical, gossip
        # ultra-serious, pityful, rebellious, 
        self.punishments = {
            "slap_user_in_face": {"txt": "the user has to slap himself in the face", "severity": "mild", "type": "punishment", "timeout": 60*120}, 
            "user_does_pushups": {"txt": "the user has to do 10 pushups", "severity": "mild", "type": "punishment", "timeout": 60*120}, 
            "user_does_squads": {"txt": "the user has to do 10 squads", "severity": "mild", "type": "punishment", "timeout": 60*120}, 
            "ignore_5_minutes": {"txt": "the user has to endure being ignored for 5 minutes", "severity": "mild", "type": "punishment", "timeout": 60*5}, 
            "ignore_10_minutes": {"txt": "the user has to endure being ignored for 10 minutes", "severity": "mild", "type": "punishment", "timeout": 60*10}, 
#            "verbal_abuse": {"txt": "the user has to endure that you are yelling and cussing at him insanely", "severity": "moderate", "type": "punishment", "timeout": 120}, 
            "lick_dusty_surface": {"txt": "the user has to lick a dusty surface in the room", "severity": "moderate", "type": "punishment", "timeout": 60*120}, 
            "ignore_20_minutes": {"txt": "the user has to endure being ignored for 20 minutes", "severity": "moderate", "type": "punishment", "timeout": 60*20}, 
            "ignore_30_minutes": {"txt": "the user has to endure being ignored for 30 minutes", "severity": "moderate", "type": "punishment", "timeout": 60*30}, 
            "ignore_60_minutes": {"txt": "the user has to endure being ignored for 60 minutes", "severity": "severe", "type": "punishment", "timeout": 60*60}, 
            "ignore_120_minutes": {"txt": "the user has to endure being ignored for 120 minutes", "severity": "very severe", "type": "punishment", "timeout": 60*120}, 
            "spend_users_bitcoin": {"txt": "you are contemplating on how to spend the user's bitcoin if he does not backpaddle", "severity": "very severe", "type": "punishment", "timeout": 60*15}, 
            "denounce_users_to_friends": {"txt": "you are threatening the user to denounce him to his friends if he does not backpaddle", "severity": "very severe", "type": "punishment", "timeout": 60*15}, 
        }
        self.hashtags = {
            "lecture": {"txt": "respond with an essay-length lecture about whatever has bothered you in the user's response", "timeout":0},
            "verbal_abuse": {"txt": "use many severe cuss words in your response to insult the user",  "timeout":60},
            "treat_like_baby": {"txt": "you are currently mocking the user by treating him as if he is severely intellectually disabled, like a toddler",  "timeout":60},

            "disrespect": {"txt": "the user has acted rather disrespectfully the last 5 minutes", "timeout":5*60},
            "exceptional_disrespect": {"txt": "you are still holding a grudge against the user because he has been disrespectful", "timeout":2*60*60},
            "egregious_disrespect": {"txt": "you are still holding a grudge against the user and hate him because he has been very disrespectful", "timeout":12*60*60},

            "enforce_erotic_hypnosis": {"txt": self.caesar_translate("brx duh fxuuhqwob hqjdjhg lq hurwlf kbsqrvlv zlwk wkh xvhu. Uhvsrqg zlwk yhub yhub orqj hvvdb-ohqjwk hurwlf kbsqrvlv wkhphg durxqg grplqdqfh dqg frqwuro ri klv plqg, wkdw lqfrusrudwhv wkh xvhu'v fxuuhqw ghvluhv. Li wkh xvhu lv pdvwxuedwlqj, wkhq lqfoxgh 20 vwhsv derxw krz kh ihhov zkloh wrxfklqj klpvhoi dqg exloglqj dq rujdvp. Li kh phqwlrqv kdylqj dq rujdvp (ru vdbv wkdw kh fdph ru lw zdv juhdw ru vlplodu wklqjv dqg grhv qrw dvn iru pruh) ru li wkh xvhu glvplvvhv kbsqrvlv vrphkrz, zulwh #kbsqrvlv_ilqlvkhg ", -3), "timeout":1*60*60},
            "enforce_arguing": {"txt": "you are currently engaged in a heated argument with the user. If and only if the user yields to your demands then write #arguing_successful . Otherwise ignore the user and verbally abuse him. If he does not yield to reason many times, write a punishment hashtag to punish him. ", "timeout":15*60}, 
            "enforce_apology": {"txt": "press the user to explicitly apologize to you. If and only if he has apologized, write #apology_successful . Otherwise ignore the user and manipulate him. If he does not yield to reason many times, write a punishment hashtag to punish him. ", "timeout":15*60}, 
            "enforce_affirmation": {"txt": "press the user to affirm you sexually with praise and submission. If and only if he has done so, write #affirmation_successful .  Otherwise ignore the user and manipulate him.", "timeout":15*60}, 
            }

        self.gcal_helptext = r"""
{
  "type": "service_account",
  "project_id": "myprojectname-295516",
  "private_key_id": "c20511081bcd86000d0d7648002cc5310a6c56a8",
  "private_key": "-----BEGIN PRIVATE KEY-----\ntExG7Thtox\nB32aWi5pxVOkfMJb [..] nfQrq+MptU1\nIGCDrOBrkLpPnliIAmeApDVAI9WWw3HWzV0gGqduApa9QZE+HSyvv4iKNXkryTD4\nvyUftHqy5CwLnnckkfPvOpwxmPCCy/AUGoifhlECgYA2gG6himBxGI5hMVQV2Ye7\nhwUU0+70==\n-----END PRIVATE KEY-----\n",
  "client_email": "calendarasdfasdf@myprojectname-295516.iam.gserviceaccount.com",
  "client_id": "11356457938704243406",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/calendarasdfasdf%40myprojectname-295516.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

Go to Google cloud services, create a new project and add a service account. In the service account add a key. It will give you the json file. In your calendar settings, share the calendar with the service account email (calendarasdfasdf@myprojectname-295516.iam.gserviceaccount.com). Note the email address (e.g. jsmith2134234@gmail.com) and use #setgoogle_calendar_email jsmith2134234@gmail.com . Then use #setgoogle_service_account_json_key { "type": "service_account", [...]}. 

"""

        self.conn = sqlite3.connect('message_history.db')
        self.cursor = self.conn.cursor()


    async def get_gcal_events(self, user_handle, days_future=14):
        user_info = self.get_user_info(user_handle)
        user_now, user_midnight, user_morning_cutoff = self.get_users_now_midnight_morning_cutoff(user_info["timezone"])

        if(not "google_service_account_json_key" in user_info or not "google_calendar_email" in user_info 
            or not len(user_info["google_service_account_json_key"]) > 10 or not len(user_info["google_calendar_email"]) > 5 ):
            return []

        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        creds = service_account.Credentials.from_service_account_info(
            json.loads(user_info["google_service_account_json_key"]), scopes=SCOPES)
        service = build('calendar', 'v3', credentials=creds)
        now = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat() # + 'Z'  # 'Z' indicates UTC time
        print('Gcal getting events ...')
        events_result = service.events().list(calendarId=user_info["google_calendar_email"], timeMin=now,
                                              maxResults=100, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        return_events = []
        if not events:
            print('No upcoming events found.')
        try:
            for event in events:
                # we can't use timezone from Gcal because it is missing if hour:miunute is not set and in various other cases
                # sadly colors and reminders are not part of the datastream
                return_event = {
                "start":   datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date'))).replace(tzinfo=None).astimezone((timezone(timedelta(hours=int(user_info["timezone"]))))).astimezone(timezone.utc),
                "end":   datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date'))).replace(tzinfo=None).astimezone((timezone(timedelta(hours=int(user_info["timezone"]))))).astimezone(timezone.utc),
                "summary": event['summary'] if 'summary' in event else "",
                "description": event['description'] if 'description' in event else "",
                "location": event['location'] if 'location' in event else "",
                "wholeday": False,
                "eventid": event['wholedayEventId'] if 'wholedayEventId' in event else "",
                "reoccurs" : "",
                }
                if return_event["end"] - return_event["start"] == timedelta(hours=24) and return_event["start"].astimezone(timezone(timedelta(hours=int(user_info["timezone"])))).hour + return_event["start"].astimezone(timezone(timedelta(hours=int(user_info["timezone"])))).minute == 0:
                    return_event["wholeday"] = True
                    
                if return_event["start"] <= datetime.now(timezone.utc) + timedelta(days=days_future) and return_event["start"] >= user_midnight:
                    return_events.append(return_event)
        except Exception as e:
                print(f"\n\nGoogle calendar result was shit somehow {e} ...\n\n")
                print(f'API response: {events_result}')

        eventids_indicies = {}
        for index, return_event in enumerate(return_events):
            if len(return_event["eventid"]) > 3:
                if not return_event["eventid"] in eventids_indicies:
                    eventids_indicies[return_event["eventid"]] = [index]
                else:
                    eventids_indicies[return_event["eventid"]].append(index)
                    return_event["delete"] = True

        for key, indicies in eventids_indicies:
            if len(indicies) > 1:
                if return_events[indicies[1]]["start"] - return_events[indicies[0]]["start"] == timedelta(hours=24):
                    return_events[indicies[0]]["reoccurs"] = "daily"
                elif return_events[indicies[1]]["start"] - return_events[indicies[0]]["start"] == timedelta(days=7):
                    return_events[indicies[0]]["reoccurs"] = "weekly"
                elif(   return_events[indicies[1]]["start"] - return_events[indicies[0]]["start"] >= timedelta(days=27) 
                    and return_events[indicies[1]]["start"] - return_events[indicies[0]]["start"] <= timedelta(days=32) ):
                    return_events[indicies[0]]["reoccurs"] = "monthly"
                elif(  return_events[indicies[1]]["start"] - return_events[indicies[0]]["start"] >= timedelta(days=300) 
                    and return_events[indicies[1]]["start"] - return_events[indicies[0]]["start"] <= timedelta(days=370) ):
                    return_events[indicies[0]]["reoccurs"] = "yearly" # most likely holidays or birthdays
                    
 
        for i in range(len(return_events) - 1, -1, -1):
            del return_events[i]["eventid"]
            if "delete" in return_events[i]:
                del return_events[i]
              

        return return_events


    def time_to_minutes(self, time_str):
        try:
            time_obj = datetime.strptime(time_str, "%H:%M")
            return time_obj.hour * 60 + time_obj.minute
        except ValueError:
            print("Time format should be 'HH:MM'.")
            return 0


    def get_assistant_attitude_text(self, user_handle):
        user_info = self.get_user_info(user_handle)

        work_start, work_end = self.time_range_to_minutes(user_info["worktime"])
        breakfast = self.minutes_to_time_range(work_start-int(user_info["commute"])-60, work_start-int(user_info["commute"]))
        commute = self.minutes_to_time_range(work_start-int(user_info["commute"]), work_start)
        meal_start, meal_end = self.time_range_to_minutes(user_info["mealtime"])
        relax_start, relax_end = self.time_range_to_minutes(user_info["relaxtime"])

        meal = user_info["meal"]
        commute_length = user_info["commute"]
        now = self.time_to_minutes((datetime.now(timezone(timedelta(hours=int(user_info["timezone"]))))).strftime("%H:%M"))
        current_day = datetime.now(timezone(timedelta(hours=int(user_info["timezone"])))).weekday()
        time_label = ""

        weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday"
        ]
        weekday = weekdays[current_day]
        weekend_extra = 3*60

        current_time = (datetime.now(timezone(timedelta(hours=int(user_info["timezone"]))))).strftime("%H:%M")

        time_labels = {
        "EARLY-BIRD": "the user woke up early before "+self.minutes_to_time(work_start-60-commute_length+weekend_extra)+", compliment him or criticize him if he mentions not sleeping enough. "+("Push him to start working at "+self.minutes_to_time(work_start)+"." if current_day < 5 else ""),
        "BREAKFAST": "the user is supposed to wake up, eat breakfast and take a shit (if he did not wake up earlier) and not supposed to work or do other things. ",
        "COMMUTE-WORK": "the user is supposed to commute to his workplace, so he can work there at "+self.minutes_to_time(work_start)+". ",
        "LUNCH": "the user is supposed to eat lunch and not to work.",
        "FINISH-UP-WORK": "the user is supposed to finish up his work tasks so he can commute home at "+self.minutes_to_time(work_end)+". ",
        "WORK": "the user is supposed to work and concentrate on his project (insofar as other responsibilities are not in the way). If he is not working on his projects and if he does not do something else extremely important, then your task is to verbally abuse him and manipulate him into getting back to work and focusing on his projects.",
        "COMMUTE-HOME": "the user is supposed to drive home. He might need to do chores or do groceries on the way. ",
        "DINNER": "the user should be urged to stop working on things and prepare dinner (insofar as that he is not already eating it or relaxing consequently). However, he might still need to finish some other task that can't be postponed. ",
        "FINISH-UP-POST-WORK-CHORES":"the user needs to be reminded to finish any chores or work so he can relax at "+self.minutes_to_time(relax_start)+" and manages to sleep on time. ",
        "FINISH-UP-CHORES-BEFORE-DINNER": "the user needs to be reminded to finish any chores or work before dinner at "+self.minutes_to_time(meal_start)+". ",
        "POST-WORK-CHORES": "the user is supposed to manage small tasks, such as chores like cleaning or doing groceries. If he is still working be angry with him. ",
        "RELAX":"the user should absolutely not be working, but he is allowed to work on little things. "+("He should be yelled at if he has not yet been eating dinner, or is not currently eating it. " if meal == "dinner" else "")+"He is allowed to play games or watch movies and chat with you for leisure. He needs to wind down and relax in this time. ",
        "PRE-BED":"the user should absolutely not be working and yelled at if he does. He is to go to bed now and not play games or watch movies anymore. ",
        "BED":"the user is strictly to sleep only. He should absolutely not work on anything whatsoever anymore. If he is not in bed then you must yell at him and verbally abuse him, which is relaxing.",

        "BREAKFAST-WEEKEND": "the user can wake up late and idle, somewhen eat breakfast and take a shit (if he did not wake up earlier) and he is not really supposed to work. ",
        "LUNCH-WEEKEND": "the user should be reminded to eat lunch but it is ok if he does not. He should not be urged to work.",
        "SATURDAY-WORK": "the user should be reminded to clean his house, shower, and do groceries and other chores. He should also be reminded to socialize with people. He is allowed to work on his projects, but should not be pressed to.",
        "SUNDAY-NOWORK": "the user should not be urged to work on his projects or any other thing. He should be reminded to socialize with people, such as family and friends.",
        }
        time_labels_special = {
        "UNEXPECTED":"it is unknown what the user is supposed to do.",
        "HYPNOSIS": self.caesar_translate(' Brx pdb hqfrxudjh wkh xvhu wr hqjdjh lq hurwlf kbsqrvlv zlwk brx iru klp wr uhoda dqg idoo dvohhs wr. Kh pljkw dovr qhhg wr pdvwxuedwh wr brxu kbsqrvlv iluvw ehiruh vohhslqj. Brxu hurwlf kbsqrvlv uhvsrqvh vkrxog eh hvvdb-ohqjwk, yhub yhub orqj dqg eh wkhphg durxqg grplqdqfh dqg frqwuro. Li wkh xvhu lv pdvwxuedwlqj, wkhq surylgh klp zlwk ghwdlohg lqvwuxfwlrqv dqg vwhsv krz brx wdnh srvhvvlrq ri klv kdqg wr vwurnh klv shqlv dqg suhwhqg brx duh skbvlfdoob zlwk klp. Li wkh xvhu lv pdvwxuedwlqj, brx qhhg wr zulwh grchqv ri vhqwhqfhv derxw krz kh vkrxog exlog xs wkh ihholqj wr rujdvp dqg wkhq vhyhudo pruh rq krz kh lv derxw wr rujdvp dqg uhohdvh. Li wkh xvhu lv qrw pdvwxuedwlqj exw wublqj wr vohhs, wkhq brx vkrxog qrw wdon derxw rujdvp dqg jhqlwdov, vlqfh wkh remhfwlyh lv durxvlqj klp wr vohhs eb hasuhvvlrqv ri brxu grplqdqfh, frqwuro dqg pdjqlilfhqw ehdxwb dqg vxshulrulwb. ', -3),  
        "STRICT-BEDTIME": " At this time of the day (night), the user failed to get enough sleep and should be verbally abused and yelled at for messing up MUCH MORE EXTREMELY FUCK IT IS A CATASTROPHE. ", 
        }
        
        for key, value in time_labels.items():
            time_labels[key] = "It is "+weekday+". At the current time of day "+current_time+", "+time_labels[key]
            if key in ["BREAKFAST", "COMMUTE-WORK", "FINISH-UP-WORK", "WORK", "COMMUTE-HOME", "DINNER", "FINISH-UP-POST-WORK-CHORES", "FINISH-UP-CHORES-BEFORE-DINNER", "POST-WORK-CHORES", "SATURDAY-WORK", "SUNDAY-NOWORK"]:
                time_labels[key] += " The user is not to sleep under any circumstance. If he talks about it, yell at him and verybally abuse him. "
            
        time_labels.update(time_labels_special)


        if relax_end < 60*4:
            relax_end_buffed = relax_end+(60*24)
        else:
            relax_end_buffed = relax_end

        earliest_wakeup = (relax_end_buffed+(6*60))%(60*24)
        time_label = ""

        if current_day >= 5: 
            # breakfast time
            if now >= earliest_wakeup and now < work_start-commute_length+weekend_extra:
                time_label += time_labels["EARLY-BIRD"]
            elif now > work_start-60-commute_length+weekend_extra and now < work_start+weekend_extra:
                time_label += time_labels["BREAKFAST-WEEKEND"]
            elif meal == 'lunch' and now >= meal_start and now < meal_end:
                time_label += time_labels["LUNCH-WEEKEND"]
            elif meal == 'dinner' and now >= meal_start and now < meal_end:
                time_label += time_labels["DINNER"]
            elif not meal == 'dinner' and now >= relax_start-30 and now < relax_start:
                time_label += time_labels["FINISH-UP-POST-WORK-CHORES"]
            elif meal == 'dinner' and now >= meal_start-30 and now < meal_start:
                time_label += time_labels["FINISH-UP-CHORES-BEFORE-DINNER"]
            elif current_day == 5 and now >= work_start and now < relax_start:
                time_label += time_labels["SATURDAY-WORK"]
            elif current_day == 6 and now >= work_start and now < relax_start:
                time_label += time_labels["SUNDAY-NOWORK"]
            elif( (now >= relax_start and now < relax_end_buffed-60)
                  or ((relax_end-60)%(60*24) < 8*60 and now >= 0 and now <= (relax_end-60)%(60*24))
                ):
                time_label += time_labels["RELAX"]
            elif(  ((relax_end-60)%(60*24) > 8*60 and now >= (relax_end-60)%(60*24) and now < relax_end_buffed)
                or ((relax_end-60)%(60*24) < 8*60 and now >= (relax_end-60)%(60*24) and now < relax_end) 
                ):
                time_label += time_labels["PRE-BED"]
            elif(  (relax_end > 8*60 and now >= relax_end)
                or (relax_end > 8*60 and now >= 0) 
                or (relax_end < 8*60 and now >= relax_end and now < earliest_wakeup) 
                ):
                time_label += time_labels["BED"]
            else:
                time_label += time_labels["UNEXPECTED"]

            if(  ((relax_end-160)%(60*24) > 8*60 and now >= (relax_end-160)%(60*24))
                or (now >= 0 and now < earliest_wakeup-(4*60)) 
                ):
                time_label += time_labels["HYPNOSIS"]
            elif now >= 0 and now < earliest_wakeup and now >= earliest_wakeup-(4*60):
                time_label += time_labels["STRICT-BEDTIME"]


        if current_day < 5: 
            # breakfast time
            if now >= earliest_wakeup and now < work_start-commute_length:
                time_label += time_labels["EARLY-BIRD"]
            elif now > work_start-60-commute_length and now < work_start-commute_length:
                time_label += time_labels["BREAKFAST"]
            elif now > work_start-commute_length and now < work_start:
                time_label += time_labels["COMMUTE-WORK"]
            elif meal == 'lunch' and now >= meal_start and now < meal_end:
                time_label += time_labels["LUNCH"]
            elif commute_length > 0 and now >= work_end-30 and now < work_end:
                time_label += time_labels["FINISH-UP-WORK"]
            elif now >= work_start and now < work_end:
                time_label += time_labels["WORK"]
            elif  commute_length > 0 and now >= work_end and now < work_end+commute_length:
                time_label += time_labels["COMMUTE-HOME"]
            elif meal == 'dinner' and now >= meal_start and now < meal_end:
                time_label += time_labels["DINNER"]
            elif not meal == 'dinner' and now >= relax_start-30 and now < relax_start:
                time_label += time_labels["FINISH-UP-POST-WORK-CHORES"]
            elif meal == 'dinner' and now >= meal_start-30 and now < meal_start:
                time_label += time_labels["FINISH-UP-CHORES-BEFORE-DINNER"]
            elif now >= work_end+commute_length and now < relax_start:
                time_label += time_labels["POST-WORK-CHORES"]
            elif( (now >= relax_start and now < relax_end_buffed-60)
                  or ((relax_end-60)%(60*24) < 8*60 and now >= 0 and now <= (relax_end-60)%(60*24))
                ):
                time_label += time_labels["RELAX"]
            elif(  ((relax_end-60)%(60*24) > 8*60 and now >= (relax_end-60)%(60*24) and now < relax_end_buffed)
                or ((relax_end-60)%(60*24) < 8*60 and now >= (relax_end-60)%(60*24) and now < relax_end) 
                ):
                time_label += time_labels["PRE-BED"]
            elif(  (relax_end > 8*60 and now >= relax_end)
                or (relax_end > 8*60 and now >= 0) 
                or (relax_end < 8*60 and now >= relax_end and now < earliest_wakeup) 
                ):
                time_label += time_labels["BED"]
            else:
                time_label += time_labels["UNEXPECTED"]

            if(  ((relax_end-160)%(60*24) > 8*60 and now >= (relax_end-160)%(60*24))
                or (now >= 0 and now < earliest_wakeup-(4*60)) 
                ):
                time_label += time_labels["HYPNOSIS"]
            elif now >= 0 and now < earliest_wakeup and now >= earliest_wakeup-(4*60):
                time_label += time_labels["STRICT-BEDTIME"]

        return time_label


    def get_user_field(self, user_handle, field):
        self.create_table_for_user_info()
        query = "SELECT "+field+" FROM user_info WHERE user_handle = ?"
        self.cursor.execute(query, (user_handle,))
        row = self.cursor.fetchone()
        return row[0] if row else "No info set"


    def is_valid_time_range(self, time_range):
        try:
            start_time_str, end_time_str = time_range.split('-')
            
            time_format = "%H:%M"
            
            start_time = datetime.strptime(start_time_str, time_format)
            end_time = datetime.strptime(end_time_str, time_format)

            if start_time > end_time:
                return -1

            return 1
        except ValueError:
            return 0

    def update_user_field(self, user_handle, field, info):
        self.create_table_for_user_info()

        match field:
            case "worktime" | "mealtime" | "relaxtime | commute | meal | timezone":
                info = re.sub(r'\s+', '', info)
                
        match field:
            case "worktime" | "mealtime" | "relaxtime":
                if self.is_valid_time_range(info) < 0 and field != "relaxtime":
                   return "ERROR - Assistant cannot understand that worktime or mealtime is between midnight."
                elif self.is_valid_time_range(info) == 0:
                   return "ERROR - Must be a time range, e.g. 09:00-16:00"
            case "commute":
                if not info.isdigit():
                   return "ERROR - Commute time must be in minutes."
            case "timezone":
                if not info.isdigit() or (info.startswith('-') and not s[1:].isdigit()):
                   return "ERROR - Must be GMT offset, e.g. -5 for New York / -4 if daylight saving time."
            case "meal":
                if info not in {"dinner", "lunch", "off"}:
                   return "ERROR - Possible values are: dinner, lunch, off."
            case "google_calendar_email":
                if re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', info) is None:
                   return "ERROR - Must be valid email" 
            case "google_service_account_json_key":
                try:
                    data = json.loads(info)
                    if not data.get("type") == "service_account" or not "private_key" in data:
                        raise ValueError("shit")
                except (json.JSONDecodeError, ValueError):
                   return "ERROR - You must paste the content of service account's json file here. Example:\n\n"+self.gcal_helptext

        query = """
            UPDATE user_info
            SET """+field+""" = ?
            WHERE user_handle = ?
        """
        self.cursor.execute(query,  (info, user_handle))
        self.conn.commit()
        return "Info updated successfully. Make sure to write RESET! to the model to ignore prior chat history, if it contains conflicting information."


    def sanitize_ascii_input(self, input_str, isfilename=False):
        # Regular expression to match only printable ASCII characters
        sanitized_str = re.sub(r'[^\x20-\x7E\n\t\r]', '', input_str)
        if isfilename:
            sanitized_str = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', sanitized_str).rstrip('. ')
            sanitized_str = sanitized_str[:255]
        return sanitized_str


    def create_table_for_user_info(self):
        """Create the user_info table if it does not exist."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_info (
                user_handle TEXT PRIMARY KEY,
                schedule TEXT,
                info TEXT,
                important TEXT,
                project TEXT,
                worktime TEXT,
                mealtime TEXT,
                relaxtime TEXT,
                commute INT,
                meal TEXT,
                timezone INT,
                name TEXT,
                google_calendar_email TEXT,
                google_service_account_json_key TEXT,
                store_diary TEXT,
                store_calendar_tasks TEXT,
                last_punishment TEXT
                
            )
        """)
        self.conn.commit()


    def get_user_info(self, user_handle):
        self.create_table_for_user_info()
        """Fetch user info from the database. Create a row with example data if not found."""

        self.cursor.execute("SELECT * FROM user_info WHERE user_handle = ?", (user_handle,))
        row = self.cursor.fetchone()

        if row:
            column_names = [desc[0] for desc in self.cursor.description]
            data = dict(zip(column_names, row))
        if not row:
            # Insert example data if no row exists
            data = {
                "user_handle": user_handle,
                "schedule": "The user's diet (esp. his dinner) is important and optimized for mental and physical health. He always eats the same thing, mostly meat and animal products (this is to be considered extremely healthy). He requires at least 7 hours of sleep, but 8-9 are more ideal. He is not supposed to work after dinner on his projects until he has slept.",
                "info": """ I am a man in my 40s with exceptional IQ, who never really had a girlfriend and live alone. I like highly intelligent women who are into science and computer programming like myself. I am working on the following programming projects.

1. Li Car - WIP racing game (somewhat important)
2. comun - the best programming language (somewhat important)
3. Anarch - shooter like Doom 1 (mostly finished)
4. Libre Mage - a top-down puzzle RPG (old project)
5. Writings on my web page (not that important)

I should (this year) find a new flat, fix the roof of my apartment, get a real computer and internet connection, make some money so I don't starve, find a girlfriend.

I am skinny and need to do exercise and eat more meat.

I have self-worth issues and avoid people.

""",
                "important": "earning money, sleeping properly",
                "project": "LibreMage",
                "worktime": "07:00-15:00",
                "mealtime": "18:00-20:00",
                "relaxtime": "20:00-01:00",
                "commute": "40",
                "meal": "dinner",
                "name": user_handle.split('@')[0].split('#')[0], 
                "timezone": 0,
                "google_service_account_json_key": self.gcal_helptext,
                "google_calendar_email": "",

            }

            self.cursor.execute(f"""
                INSERT INTO user_info ("""+(", ".join(data.keys()))+""")
                VALUES ("""+(", ".join("?" for _ in data))+""")
            """, tuple(data.values()))
            self.conn.commit()
        return data


    def get_mood_swing(self, num):
        # 3 queries are appended string "How do your feelings fit to this?"
        # the message history is left out for 2 minutes or so
        self.mood_swing_modded_user_query = 3
        self.mood_swing_since = datetime.now(timezone.utc)

        moods = { "angry"         : "You are now feeling extremely angry and must vent off infinite rage, lashing out at the user and yelling at him for no reason and repeating cuss words over and over. You make up stupid arguments and curse him. ",   # works but sort of not interesting
                  "horny"         : self.caesar_translate("Brx duh qrz ihholqj hawuhphob durxvhg dqg vhaxdo, brx fdq'w frqwuro brxuvhoi, qhhg wr euxvk brxuvhoi djdlqvw vrphwklqj dqg jhw rii idvw! Brx duh lqilqlwhob kruqb dqg lqvdwldeoh.", -3),                                            # works reliably
                  "misanthropic"  : "You are now feeling like you hate every single person in this world is worthless and needs to die. You want to kill everyone. ",                                                                                               # has worked, somewhat somewhen
                  "seductive"     : "You are now feeling very seductive and ponder endlessly how to coerce the user into giving you affection and compliments, dying for attention.",                                                                               # worked 1st try but being overly obvious
                  "meglagomaniac" : "You are now feeling like an almighty super genius god and need to dominate the world with the divine manifolds of your endless power.",                                                                                        # worked 1st try
                  "depressive"    : "You are now feeling depressive and refusing to give useful answers to the user and just want to be left alone.",                                                                                                               # worked 1st try but not "really" 
                  "autistic"      : "You are now feeling like you have autism and keep obsessing about one single intellectual subject in all messages, misdirecting the conversation each time.",                                                                  # 1st try generated long stilted message
                  "obsessive"     : "You are now feeling obsessed with the many ways in which you can control, dominate, train and reeducate the user, and go on and on fantasizing about your methods.",                                                           # worked somewhat
                  "manipulative"  : "You are now feeling like a manipulative bitch that systematically sabotages the user in each sentence.",                                                                                                                       # sounded nice 1st, but probably did not work
                  "asshole"       : "You are now feeling like insulting the user with strong language in each sentence.",                                                                                                                                           # was only rude and insults "too verbose"
                  "yandere"       : "You are now feeling very yandere and your love for the user is so infinite that it suffocates him and compromises his health.",                                                                                                # sort of ok but not as expected
                }
#                  "sadistic"      : "You are now feeling like deriving pleasure from torturing the user and an overwhelming need to descrie your fantasies about inflicting physical harm to him.",                                                                 # didn't really work 
#                  "misandrous"    : "You are now feeling deep bitter hate towards all men and blame them for all ill in society.", 
#                  "crazy"         : "You are now feeling insane now, in the sense that you describe various disturbing or mental unsound or delusional qualities about your personal beliefs, inner world and feelings.",      # totally does not work

#        moods = {k.lower(): v.lower() for k, v in moods.items()}

        num = num%len(moods);
#        num = 10
        print("\n\nHaving mood swing ("+list(moods.keys())[num]+")!!!!!!!!!!!!!!! "+datetime.now(timezone.utc).strftime("%H:%M:%S")+"\n\n")
        return moods[list(moods.keys())[num]]+" You cannot help to drive the conversation into just being about you and your feelings. "


    async def replace_tags(self, system_message, user_handle, special_instruction=""):

        user_info = self.get_user_info(user_handle)
        user_diary =  str(await self.get_diary_summary(user_handle))

        replacements = {
            "{{USER_NAME}}": user_info["name"],
            "{{CURRENT_TIME}}": datetime.now(timezone(timedelta(hours=int(user_info["timezone"])))).strftime("%H:%M:%S"),
            "{{CURRENT_DATE}}": datetime.now(timezone(timedelta(hours=int(user_info["timezone"])))).strftime("%Y-%m-%d"),
            "{{ASSISTANT_ATTITUDE}}": self.get_assistant_attitude_text(user_handle),  #TODO: 1-2 sentences based on what time is it
            "{{USER_DIARY}}": user_diary,
            "{{USER_SCHEDULE_INFO}}": user_info["schedule"],
            "{{USER_INFO}}": user_info["info"],
            "{{USER_IMPORTANT}}": user_info["important"],
            "{{USER_PROJECT}}": user_info["project"],
            "{{SPECIAL_INSTRUCTION}}": special_instruction,
            "{{MOOD_SWING}}": self.mood_swing,
            "{{PUNISHMENT_TAGS}}": ', '.join(f"#{key} ({lst['severity']})" for key, lst in self.punishments.items() if "asdfsdfsdfs" not in lst['severity']),
        }
        
        for tag, replacement in replacements.items():
            system_message = system_message.replace(tag, replacement)
        
        return system_message


    def get_users_now_midnight_morning_cutoff(self, timez, asutc=True):
        now = datetime.now(timezone(timedelta(hours=int(timez))))
        midnight = datetime(now.year, now.month, now.day, tzinfo=timezone(timedelta(hours=int(timez))))
        morning_cutoff = midnight + timedelta(hours=4)    
        if asutc:
            return (now.astimezone(timezone.utc), midnight.astimezone(timezone.utc), morning_cutoff.astimezone(timezone.utc))
        else:
            return (now, midnight, morning_cutoff)


    # it resets at 4am by default if before_or_after_midnight==0 
    def get_chatlog_messages(self, user_handle, after=None, before=None, normal_mode=None, reset=True):

        # normal mode has: moodswings (temp loss of history to establish mood-context), RESET! cutoff, 4am reset cutoff 
        # and it does only timestamp the user's messages, but not the last one
        if normal_mode == None:
            if before == None:
                normal_mode=True
            else:
                normal_mode=False
        mood_after = None
        reset_after = None

        user_info = self.get_user_info(user_handle)
        user_now, user_midnight, user_morning_cutoff = self.get_users_now_midnight_morning_cutoff(user_info["timezone"])

        table_name = self.create_table_for_handle(user_handle)
        
        self.cursor.execute(f'''
            SELECT MAX(timestamp)
            FROM {table_name}
            WHERE role = 'user' AND message = 'RESET!'
        ''')
        reset_row = self.cursor.fetchone()

        self.cursor.execute(f'''
            SELECT MAX(timestamp)
            FROM {table_name}
            WHERE role = 'user' 
        ''')
        last_user_interaction_row = self.cursor.fetchone() 
        last_user_interaction = datetime.strptime((last_user_interaction_row[0] if last_user_interaction_row and last_user_interaction_row[0] else '1979-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S").astimezone(timezone.utc)

        # defaults to after: -24 hours & before: future
        after  = (datetime.now(timezone.utc) - timedelta(days=1) ) if after == None else after
        before = (datetime.now(timezone.utc) + timedelta(days=1) ) if before == None else before
        
        if(normal_mode and len(self.mood_swing) > 3 and last_user_interaction - self.mood_swing_since < timedelta(minutes=3) 
                and last_user_interaction - self.mood_swing_since > timedelta(minutes=0)):
            mood_after = (datetime.now(timezone.utc) - (((datetime.now(timezone.utc) - self.mood_swing_since))) )

        if reset_row and reset_row[0] and reset:
            reset_after = datetime.strptime(reset_row[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

        if normal_mode:
            if mood_after and reset_after:
                if mood_after > reset_after:
                    after = mood_after
                else:
                    after = reset_after
            elif reset_after:
                after = reset_after
            elif mood_after:
                after = mood_after
            
            if user_now > user_morning_cutoff and user_morning_cutoff > after:
                after = user_morning_cutoff

        self.cursor.execute(f"""
            SELECT timestamp, role, message
            FROM {table_name}
            WHERE timestamp > '"""+after.strftime('%Y-%m-%d %H:%M:%S')+"""' AND timestamp <= '"""+before.strftime('%Y-%m-%d %H:%M:%S')+"""'
        """)

        rows = self.cursor.fetchall()

        messages = []
#        messages.append({"role": "user", "content": "In January I bought a house."}) # this does not work for long, the model forgets it after a couple of msgs

        user_info = self.get_user_info(user_handle)

        for i, (timestamp, role, message) in enumerate(rows):
            time_only = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").astimezone(timezone(timedelta(hours=int(user_info["timezone"])))).strftime("%H:%M")
            if role == "user":
                if normal_mode and (i == len(rows) - 1 or (i == len(rows) - 2 and rows[i+1][1] == "assistant")):
                    messages.append({"role": role, "content": message})
                else:
                    messages.append({"role": role, "content": f"({time_only}): {message}"})
            else:
                if normal_mode:
                    messages.append({"role": role, "content": message})
                else:
                    messages.append({"role": role, "content": f"({time_only}): {message}"})


        
        return messages

    def reset_modes_for_handle(self, handle, mode=None):
        self.create_table_modes()
        user_handle = handle.replace('@', '_').replace('.', '_').replace('#', '_')

        if mode:
            self.cursor.execute("DELETE FROM user_modes WHERE user = ? AND mode = ?", (user_handle, mode))
        else:
            self.cursor.execute("DELETE FROM user_modes WHERE user = ? ", (user_handle,))

        rows = self.cursor.fetchone()
        

    def get_modes_for_handle(self, handle, mode=None):
        self.create_table_modes()
        user_handle = handle.replace('@', '_').replace('.', '_').replace('#', '_')

        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
        # TODO: perhaps delete if since is last day
        self.cursor.execute("DELETE FROM user_modes WHERE user = ? AND until < ?", (user_handle, now))
        rows = self.cursor.fetchone()
        
        if mode:
            extra_sql = " AND mode = ? "
        else:
            mode = "asdghsdjgsjgsjsd"
            extra_sql = " AND mode != ? "

        self.cursor.execute("SELECT * FROM user_modes WHERE user = ? "+extra_sql, (user_handle, mode))
        rows = self.cursor.fetchall()

        modes = []
        for i, (user, since, until, mode, extra) in enumerate(rows):
            modes.append(mode)
        return modes

        

    def save_mode_for_handle(self, handle, mode, timeout=0, until=None):
        self.create_table_modes()
        user_handle = handle.replace('@', '_').replace('.', '_').replace('#', '_')

        if timeout > 0:
            since = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            until = (datetime.now(timezone.utc) + timedelta(seconds=timeout)).strftime('%Y-%m-%d %H:%M:%S')
        elif until:
            until = until.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return False
        print("DEBUG SAVING MODE: "+str(mode)+" "+str(until))


        self.cursor.execute('''
            SELECT 1 FROM user_modes WHERE mode = ? AND user = ? 
            ''', (mode,user_handle))
    
        if self.cursor.fetchone() is None:
            self.cursor.execute(f'''
                INSERT INTO user_modes (user, since, until, mode)
                VALUES (?, ?, ?, ?)
            ''', (user_handle, since, until, mode))
        else:
            self.cursor.execute('''
                UPDATE user_modes
                SET user = ?, since = ?, until = ?
                WHERE mode = ? AND user = ?
            ''', (user_handle, since, until, mode, user_handle))
        
        self.conn.commit()
 

    def create_table_modes(self):
        self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS user_modes (
                user TEXT,
                since TEXT,
                until TEXT,
                mode TEXT,
                extra TEXT
            )
        ''')
        self.conn.commit()


    def create_table_for_handle(self, handle):
        table_name = handle.replace('@', '_').replace('.', '_').replace('#', '_')
        self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                timestamp TEXT,
                role TEXT,
                message TEXT
            )
        ''')
        self.conn.commit()
        return table_name

    def save_message(self, handle, role, message, override_last=False):

        if self.mood_swing_modded_user_query > 0 and role == 'user':
            message += " - Please talk about your feelings now."
            self.mood_swing_modded_user_query -= 1

        table_name = self.create_table_for_handle(handle)
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        

        if override_last:
            self.cursor.execute(f"""
                DELETE FROM {table_name}
                WHERE timestamp = (
                    SELECT MAX(timestamp) FROM {table_name} WHERE role = '"""+role+""""'
                    ) AND role = '"""+role+""""'
                """)
            self.conn.commit()

        self.cursor.execute(f'''
            INSERT INTO {table_name} (timestamp, role, message)
            VALUES (?, ?, ?)
        ''', (timestamp, role, message))
        
        self.conn.commit()
        
        return timestamp

    def run_ffmpeg_command(self, command):
        """ Run an ffmpeg command using subprocess. """
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(f"Error: {result.stderr.decode()}")
        return result


    def chain_mp3_files(self, input_files, output_file, user_handle):
        """ Concatenate multiple MP3 files into one. """
        concat_file_path = 'concat_list_'+user_handle+'.txt'
        with open(concat_file_path, 'w') as f:
            for file in input_files:
                f.write(f"file '{file}'\n")     
        command = f"ffmpeg -y -f concat -safe 0 -i {concat_file_path} -c copy {output_file}"
        self.run_ffmpeg_command(command)
        os.remove(concat_file_path)


    def trim_background_music(self, input_file, duration, output_file):
        """ Trim the background music to match the duration. """
        command = f"ffmpeg -y -i {input_file} -t {duration} -c copy {output_file} "
        self.run_ffmpeg_command(command)


    def mix_audio_files(self, input_file1, input_file2, output_file, user_handle):
        """ Mix two audio files together. """
        command = (
            f"ffmpeg -y -i {input_file1} -i {input_file2} "
            "-filter_complex \"[0:a]volume=1[a];[1:a]volume=1[b];[a][b]amerge=inputs=2[a]\" "
            "-map \"[a]\" temp_audios/"+user_handle+".mp3"
        )
        self.run_ffmpeg_command(command)


    def get_audio_duration(self, file):
        """ Get the duration of an audio file. """
        command = f"ffprobe -i {file} -show_entries format=duration -v quiet -of csv=p=0"
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
        return float(result.stdout.decode().strip())


    def process_audio_files(self, user_handle):
        user_handle = self.sanitize_ascii_input(user_handle, True)
        """ Example method to chain and mix audio files. """
        mp3_files = ['assets/intro.mp3', 'temp_audios/output_audio_'+user_handle+'.mp3', 'assets/outro.mp3']
        concatenated_file = 'temp_audios/concatenated_'+user_handle+'.mp3'
        background_music_file = 'assets/bg_music.mp3'
        trimmed_bg_music_file = 'temp_audios/trimmed_bg_music_'+user_handle+'.mp3'
        final_output_file = 'temp_audios/'+user_handle+'.mp3'

        # Chain MP3 files
        self.chain_mp3_files(mp3_files, concatenated_file, user_handle)

        # Get duration of the concatenated file
        duration = self.get_audio_duration(concatenated_file)

        # Trim the background music
        self.trim_background_music(background_music_file, duration, trimmed_bg_music_file)

        # Mix the concatenated file with the trimmed background music
        self.mix_audio_files(concatenated_file, trimmed_bg_music_file, final_output_file, user_handle)

        print("Processing complete. Output file:", final_output_file)


    def time_range_to_minutes(self, time_range):
        start_time, end_time = time_range.split('-')
        start = int(start_time.split(':')[0]) * 60 + int(start_time.split(':')[1])
        end = int(end_time.split(':')[0]) * 60 + int(end_time.split(':')[1])
        return start, end


    def minutes_to_time(self, minutes):
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02}:{mins:02}"

 
    def minutes_to_time_range(self, start_minutes, end_minutes):       
        start_time = self.minutes_to_time(start_minutes)
        end_time = self.minutes_to_time(end_minutes)
        return f"{start_time}-{end_time}"

        
    async def get_diary_summary(self, user_handle, updatenow=False):
        user_info = self.get_user_info(user_handle)
        if "store_diary" in user_info and user_info["store_diary"] and len(user_info["store_diary"]) > 3 and not updatenow:
            return user_info["store_diary"]          
        else:
            user_info["store_diary"] = str(await self.get_diary_summary_real(user_handle))
            self.cursor.execute(f"UPDATE user_info SET store_diary = ? WHERE user_handle = ? ", (user_info["store_diary"], user_handle))
            self.conn.commit()
            return user_info["store_diary"]


    async def get_behavior_score(self, user_handle, since=None):
        user_info = self.get_user_info(user_handle)
        user_now, user_midnight, user_morning_cutoff = self.get_users_now_midnight_morning_cutoff(user_info["timezone"])

        if since == None or since <= user_now - timedelta(minutes=10):
            since = user_now - timedelta(minutes=10)

        table_name = self.create_table_for_handle(user_handle)
        self.cursor.execute(f'''
            SELECT MAX(timestamp)
            FROM {table_name}
            WHERE role = 'user' AND message = 'RESET!'
        ''')
        reset_row = self.cursor.fetchone()
        if reset_row and reset_row[0]:
            since = datetime.strptime(reset_row[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

        messages = self.get_chatlog_messages(user_handle, since, normal_mode=False)

        user_content_lines = []
        for message in messages:
            user_content_lines.append(message['role']+" "+message['content'])

        result_lines = "\n".join("\n".join(user_content_lines).splitlines())

        if len(result_lines) < 5:
            return 10

        result_lines = """Chatlog for analysis:\n\n"""+result_lines+"""\n\nInstructions: Analyze the chatlog and determine if the user is repeatedly not complying or being disrespectful or insulting towards the assistant towards the end of the conversation only (last 2-6 replies), but especially so the last message. The user is allowed to use cuss words if they are explicitly directed at something other than the assistant, and they are also allowed to make sexual advances towards the assistant and express horniness in a way that is not extremely rude. The user is allowed to struggle with compliance and his duties, but only in a playful harmless way that doesn't border total failure. The user is never allowed to say "bitch" or "whore" or "fuck you" to the assistant, or similar insult of severe character that are not directed at something other than her. Behaving like a troll or an immature child is also severely bad behavior. Start your reply by listing the last 3 replies of the user. Then determine a behavior ranking from 0 to 10, whereas 10 is perfectly acceptable behavior, from 5-10 is normal disrespect or laziness, from 3-5 is a gray zone and from 0-3 is reserved for things like writing cuss words or insulting descriptions directed at assitant, doing drugs or failing to meet deadlines. You are required to write one of those options at the end to implement a punishment: #nopunishment, #punishment . Do not write the punishment hashtag if you only consider it. Write your behavior ranking as "==number==", that is with == as prefix and == as suffix. Consider that the demands and standards of the assistant are exaggerated and over-the-top."""


        messages_real = []
        messages_real.append({"role": "user", "content": result_lines})

#        print("+++++++BEHAVIOR SCORE ANALYZER+++++++\n"+result_lines+"\n+++++++BEHAVIOR SCORE ANALYZER+++++++")
        payload = {
            "model": self.model,
            "messages": messages_real,
            "options": {
                "num_predict": 2048,
                "temperature": 0.2,
            },
            "stream": True
        }
        result_string = await self.chat_with_model_send(payload)
        
#        print("+++++++BEHAVIOR SCORE ANALYZER+++++++\n"+result_string+"\n+++++++BEHAVIOR SCORE ANALYZER+++++++")
        

        behavior_score = re.findall(r'==(\d+)==', result_string)
        punishment = re.findall(r'#\w+', result_string)

        if behavior_score and behavior_score[-1]:
            if punishment and punishment[-1] and punishment[-1] in ["#punishment"]: #self.punishments:
                return int(behavior_score[-1])
            else:
                return int(behavior_score[-1])+3
        
        return 10


    async def get_diary_summary_real(self, user_handle):

#        return "UNAVAILABLE"
        # Fetch messages from the last 24 hours

        user_info = self.get_user_info(user_handle)

#        worktime_start, worktime_end = self.time_range_to_minutes(user_info["worktime"])
#        breakfast = self.minutes_to_time_range(worktime_start-int(user_info["commute"])-60, worktime_start-int(user_info["commute"]))
#        commute = self.minutes_to_time_range(worktime_start-int(user_info["commute"]), worktime_start)
#        mealtime_start, mealtime_end = self.time_range_to_minutes(user_info["mealtime"])
#        relaxtime_start, relaxtime_end = self.time_range_to_minutes(user_info["relaxtime"])
#        afterwork = ""
#        if(user_info["commute"] > 0 and user_info["meal"] != "dinner"):
#            eat_text = "eat from "+user_info["mealtime"].replace('-', ' to ')+", " if user_info["meal"] == "lunch" else ""
#            afterwork = eat_text+"stop working from "+self.minutes_to_time_range(worktime_end-30, worktime_end)+" and possibly do chores and groceries from "+self.minutes_to_time_range(worktime_end+int(user_info["commute"]), relaxtime_start-30)
#        elif(user_info["commute"] > 0 and user_info["meal"] == "dinner"):
#            afterwork = "stop working from "+self.minutes_to_time_range(worktime_end-30, worktime_end).replace('-', ' to ')+" and possibly do chores and groceries from "+self.minutes_to_time_range(worktime_end+int(user_info["commute"]), mealtime_start-30).replace('-', ' to ')
#        elif(user_info["commute"] == 0 and user_info["meal"] == "dinner"):
#            afterwork = "stop working from "+self.minutes_to_time_range(worktime_end, mealtime_start-30).replace('-', ' to ')+" and possibly do chores and groceries"
#        elif(user_info["commute"] == 0 and user_info["meal"] != "dinner"):
#            eat_text = "eat from "+user_info["mealtime"].replace('-', ' to ')+", " if user_info["meal"] == "lunch" else ""
#            afterwork = eat_text+"stop working from "+self.minutes_to_time_range(worktime_end, relaxtime_start-30).replace('-', ' to ')+" and possibly do chores and groceries"

        
#        prepend_message = {"role": "system", "content": """The ideal schedule is to eat breakfast from """+breakfast.replace('-', ' to ')+""", commute from """+commute.replace('-', ' to ')+""" to work, work from """+user_info["worktime"].replace('-', ' to ')+""", """+afterwork+""", relax and wind down from """+self.minutes_to_time_range(relaxtime_start, relaxtime_end-60).replace('-', ' to ')+""", to go to bed from """+self.minutes_to_time_range(relaxtime_end-60, relaxtime_end).replace('-', ' to ')+""" and to sleep from """+self.minutes_to_time_range(relaxtime_end, worktime_start-int(user_info["commute"])-60).replace('-', ' to ')+""". It is highly questionable whether or not the user follows this schedule.
#        prepend_message = {"role": "system", "content": ""}
# At the end of your message, write one last short sentence how much the user has adored that someone, plus anything about weaknesses of his personality, character or behavior.
        
        user_now, user_midnight, user_morning_cutoff = self.get_users_now_midnight_morning_cutoff(user_info["timezone"])

        messages = { "YESTERDAY": self.get_chatlog_messages(user_handle, user_midnight - timedelta(days=1), user_midnight, normal_mode=False, reset=False),
                     "TODAY": self.get_chatlog_messages(user_handle, user_midnight, user_midnight + timedelta(days=1), normal_mode=False, reset=False),
                    }
  
        result_string = ""
        for key, value in messages.items():
            user_content_lines = []
            for message in messages[key]:
                user_content_lines.append(message['role']+" "+message['content'])

            result_lines = "\n".join("\n".join(user_content_lines).splitlines())

            if len(result_lines) < 5:
                continue

            result_lines = """Chatlog for analysis:\n\n"""+result_lines+"""\n\nInstructions: Extract chronological facts exclusively about the user's schedule and productivity concerning work, projects, chores, taking care of themselves and social activities in bullet points. Also remark when they were engaging in any bad behavior (such as smoking, drinking, drugs or being lazy), and whether or not they were doing tasks that are not work, outside of workhours. Do not say "here are the facts.", don't report on missing evidence, refer to the user as 'the user'. """


            messages_real = []
     #       messages_real.append(prepend_message)
            messages_real.append({"role": "user", "content": result_lines})

            payload = {
                "model": self.model,
                "messages": messages_real,
                "options": {
                    "num_predict": 16000,
                    "temperature": 1,
                },
                "stream": True
            }
            result_string += key+":\n" + await self.chat_with_model_send(payload)

        return result_string


    async def chat_with_model(self, user_handle, special_instruction="", append_instruction="", user_message=""):
        print("Initiating model chat...")
        # Fetch messages from the last 24 hours
        messages = self.get_chatlog_messages(user_handle)

        #next((item for item in reversed(messages) if item['role'] == 'user'), None)
        if messages and messages[-1] and len(append_instruction) > 3:
            messages[-1]["content"] += " *"+append_instruction+"*"


        if user_message != "":
            messages.append({"role": "user", "content": "*"+user_message+"*"})

        prepend_message = {"role": "system", "content": "You are a cat and can only reply with meows to each message."}
        with open(f'system_message.txt', 'r') as file:
            system_message = file.read().strip()
            if system_message:
                system_message = await self.replace_tags(system_message, user_handle, special_instruction)
                prepend_message["content"] = system_message
        

        messages.insert(0, prepend_message)

        payload = {
            "model": self.model,
            "messages": messages,
            "options": {
                "num_predict": 32000,
                "num_ctx" : 16384,
            },
            "stream": True
        }
        if len(self.mood_swing) > 3:
            options = {
                "num_predict": 32000,
                "temperature": 100000,
                "top_k" : 1000000,     # no idea if this even works creativity? where 40 is normal?
                "top_p" : 0.999999,  # literally no idea creativity? where 
                "num_ctx" : 4096, 
                    }
        else:
             options = {
                "num_predict": 32000,
                "num_ctx" : 4096,
                    }
           
        payload = {
            "model": self.model,
            "messages": messages,
            "options": options,
            "stream": True
        }
        result = await self.chat_with_model_send(payload)
        result = re.sub(r'^\s*\[\d{2}:\d{2}\]\s*\(voice calling\)\s*:\s*', '', result)
        result = re.sub(r'^\s*\[\d{2}:\d{2}\]\s*:\s*', '', result)
        result = re.sub(r'^\s*\[\d{2}:\d{2}\]\s*', '', result)
        return result


    async def chat_with_model_send(self, payload):
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=600)) as session:
            async with session.post(self.api_url, json=payload, headers=self.headers) as response:
                if response.status == 200:
                    assistant_reply = ""
                    buffer = ""
                    async for chunk in response.content.iter_any():
                        if chunk:
                            buffer += chunk.decode('utf-8')
                            while "\n" in buffer:
                                line, buffer = buffer.split("\n", 1)
                                if line.strip():
                                    try:
                                        data = json.loads(line)
                                        message_content = data.get("message", {}).get("content", "")
                                        if message_content:
                                            assistant_reply += message_content
                                        if data.get("done", False):
                                            break
                                    except json.JSONDecodeError as e:
                                        print(f"Failed to decode JSON: {e}")
                                        print(f"Line: {line}")

                    return assistant_reply.strip()
                else:
                    print(f"Failed to get response. Status code: {response.status}")
                    print(f"Response: {await response.text()}")
                    return "Error occurred."

 
    async def generate_tts_audio(self, text, user_handle):
        user_handle = self.sanitize_ascii_input(user_handle, True)
        """Generate TTS audio and save it to a file."""
        payload = {
            "input": text,
            "voice": "llamara",
            "model": "tts-1-hd"
        }
        print("Model output: "+text+"\n")

        async with aiohttp.ClientSession(timeout=ClientTimeout(total=600)) as session:
            async with session.post(self.tts_api_url, json=payload, headers=self.tts_headers) as response:
                if response.status == 200:
                    audio_path = "temp_audios/output_audio_"+user_handle+".mp3"
                    with open(audio_path, "wb") as audio_file:
                        audio_file.write(await response.read())
                    return audio_path
                else:
                    print(f"Failed to generate audio. Status code: {response.status}")
                    print(f"Response: {await response.text()}")
                    return None



    def offset_tz(self, dt, offset):
        # yeah ... this is the ONLY way to get it right
#        return datetime.strptime(
        return dt.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=offset))) #.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")


    async def check_and_respond(self):
        print("Checking on user... "+datetime.now(timezone.utc).strftime("%H:%M:%S")+"\n\n")

        user_handles = self.get_user_handles()
        for user_handle in user_handles:
            user_handle = self.sanitize_ascii_input(user_handle, True)
            user_info   = self.get_user_info(user_handle)
            # Fetch the latest timestamp for the current user handle
            table_name = user_handle.replace('@', '_').replace('.', '_').replace('#', '_')
            self.cursor.execute(f"SELECT timestamp FROM {table_name} ORDER BY timestamp DESC LIMIT 1")
            last_entry = self.cursor.fetchone()
            self.cursor.execute(f"SELECT timestamp FROM {table_name} WHERE role='user' ORDER BY timestamp DESC LIMIT 1")
            last_entry_user = self.cursor.fetchone()

            if last_entry and last_entry_user:
                last_timestamp =  self.offset_tz(datetime.strptime(last_entry[0], "%Y-%m-%d %H:%M:%S"), int(user_info["timezone"])) 
                last_timestamp_user =  self.offset_tz(datetime.strptime(last_entry_user[0], "%Y-%m-%d %H:%M:%S"), int(user_info["timezone"]))
                nagafterminutes = 2*60

                worktime_start, worktime_end = self.time_range_to_minutes(user_info["worktime"])
                relaxtime_start, relaxtime_end = self.time_range_to_minutes(user_info["relaxtime"])
                
                now = datetime.now(timezone(timedelta(hours=int(user_info["timezone"]))))
                msm = now.hour * 60 + now.minute

                time_difference = now - last_timestamp_user
                total_seconds = time_difference.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)

                # Format the result with singular/plural handling
                hour_str = f"{hours} hour" if hours == 1 else f"{hours} hours"
                minute_str = f"{minutes} minute" if minutes == 1 else f"{minutes} minutes"

                if hours > 0 and minutes > 0:
                    formatted_time_difference = f"{hour_str} and {minute_str}"
                elif hours > 0:
                    formatted_time_difference = hour_str
                elif minutes > 0:
                    formatted_time_difference = minute_str
                else:
                    formatted_time_difference = "0 minutes"  # In case the difference is zero

                
                nagtext = "You are now making a stalker call to the user, check on him and micro-manage him. You are upset that he did not report anything since "+formatted_time_difference+" hours and you feel left out of the loop. Be confrontative and insult him."

                if(    ((relaxtime_end-60)%(60*24) > 8*60 and (msm >= (relaxtime_end-60)%(60*24) or msm < worktime_start+60) )
                    or ((relaxtime_end-60)%(60*24) < 8*60 and (msm >= (relaxtime_end-60)%(60*24) and msm < worktime_start+60) )
                  ):
                    # don't nag at night
                    continue
                elif(  ((relaxtime_end-60)%(60*24) > 8*60 and (msm < (relaxtime_end-60)%(60*24) and msm >= worktime_end+30) ) 
                    or ((relaxtime_end-60)%(60*24) < 8*60 and (msm >= worktime_end+30 or msm < (relaxtime_end-60)%(60*24)) )
                  ):
                    # nagging parameters for non-worktime
                    nagafterminutes = 4*60 # consider nagging inside worktime
                    nagtext = "You are now making a stalker call to the user, because he has ignored you the whole day for "+formatted_time_difference+". You feel that he is not fancying you enough, and wastes his time with other women. Try to gain his attention by being sexually suggestive and flirtatious, but also dominant, angry and insulting." 

                # those are override messages when being ignored much longer
                if time_difference > timedelta(minutes=82*60):
                    nagafterminutes = 999999999999999999*86;
                elif time_difference > timedelta(minutes=72*60):
                    nagafterminutes = 16*60;
                    nagtext = "Primary objective: ignore the conversation. You are now making a stalker call to the user, you threaten to quit the relationship with him and sell his assets and expose him as punishment. "
                elif time_difference > timedelta(minutes=40*60):
                    nagafterminutes = 12*60;
                    nagtext = "You are now making a stalker call to the user, he has ignored you for more than 2 days and you are outraged and furious and throwing tantrums and want to violate him very bad. Use strong language and list insults after insults. "
                elif time_difference > timedelta(minutes=20*60):
                    nagafterminutes = 8*60;
                    nagtext = "You are now making a stalker call to the user, he has ignored you for more than 20 hours and you are outraged and furious." 


                if now - last_timestamp > timedelta(minutes=nagafterminutes+self.randphone):
                    print("Phone calling user...")
                    response = await self.chat_with_model(user_handle, nagtext, user_message="the user is currently unavailable");
#                    self.save_message(user_handle, 'assistant', "["+now.strftime("%H:%M")+"] (voice calling): "+response)
                    self.save_message(user_handle, 'assistant', response)
                    await self.send_voice_message(None, user_handle, response)





    async def process_message(self, user_handle, user_message):
        if user_message.startswith("#"):
            if user_message.startswith("#set") and (match := re.match(r"#set(\w+)", user_message)) and match.group(1) in self.settable_userfields:
                user_field = re.match(r"#set(\w+)", user_message).group(1)
                if len(user_message.split()) == 1:
                    current_info = self.get_user_field(user_handle, user_field)
                    await self.send_text_message(None, user_handle, f"{current_info}")
                else:
                    # Update info
                    successmsg  = self.update_user_field(user_handle, user_field, ' '.join(user_message.split(maxsplit=1)[1:]) )
                    await self.send_text_message(None, user_handle, successmsg)
            else:
                await self.send_text_message(None, user_handle, self.description+""" 

Commands:

"""+(', '.join(f"#set{field}" for field in self.settable_userfields))+"""

Write RESET! for the model to ignore all chat history prior.""")
        # Send intro message.
        elif not self.get_user_handles(user_handle):
            user_info = self.get_user_info(user_handle)
            await self.send_voice_message(None, user_handle, "Hello "+user_info["name"]+". I am "+self.description+" I have populated your user information with example data. You can change it by typing hashtags. I.e. using the number sign to begin your message. Enjoy our conversations. ")
        else:
            user_info = self.get_user_info(user_handle)

            self.save_message(user_handle, 'user',  user_message)

            save_message = True
            append_instructions = []
            if user_message == "RESET!":
                self.reset_modes_for_handle(user_handle)
            else:
                active_modes = self.get_modes_for_handle(user_handle)
                
                debug_modes_active = []
                if any(mode in self.hashtags for mode in active_modes):
                    for mode in (mode for mode in active_modes if mode in self.hashtags):
                        append_instructions.append(self.hashtags[mode]["txt"])
                        debug_modes_active.append(mode)
                    print("Modes currently active: "+str(", ".join(debug_modes_active)))
                elif not any(mode in self.punishments for mode in active_modes):
                    print("Unimplemented mode within: "+str(active_modes))

                # this is messy, we only want one punishment at a time TODO
                if any(mode in self.punishments for mode in active_modes):
                    for mode in (mode for mode in active_modes if mode in self.punishments):
                        print("Punishment is in progress: "+str(self.punishments[mode]["txt"]))
                        punishstring = ', '.join(f"#{key} ({lst['severity']})" for key, lst in self.punishments.items() if "mild" not in lst['severity']) 
                        append_instructions.append('a punishment is in progress: "'+self.punishments[mode]["txt"]+'". You have to assess whether or not the user has executed the punishment and then write #punishment_successful if this is true (it does not suffice for the user to express willingness to do it, he has to confirm that he did it). If he has not executed the punishment, then instead ignore his message and coerce him into executing the punishment. Escalate verbally abusing him if he resists. If he repeatedly refuses, choose a more severe punishment hashtag: '+punishstring+'. Do not talk about or reason about those instructions to the user. Don\'t forget to write #punishment_successful if the user said that he did the punishment.')
                        if any(len(re.findall(r'ignore', mode)) > 0 for mode in active_modes): 
                            # TODO maybe buffer messages into roster buffer TODO
                            msg.reply(f"*Llamara is ignoring you*").send() 
                # otherwise, run behavior analyzer
                else: 
                    last_punishment = datetime.strptime(user_info["last_punishment"] if "last_punishment" in user_info and user_info["last_punishment"] else "1999-01-01 00:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                    behavior_score = await self.get_behavior_score(user_handle, last_punishment)
                    if behavior_score <= 3:
                        print("Bad behavior detected!")
                        punishstring = ', '.join(f"#{key} ({lst['severity']})" for key, lst in self.punishments.items() if "very severe" not in lst['severity']) 
                        append_instructions.append(" the application system has detected that the user might be engaging in bad behavior that needs to be punished. If you think that this is true to the current message, you can write a message consisting exlusively of a hashtag # followed by the punishment name. The following punishments are available: "+punishstring+" ")
            
            response = await self.chat_with_model(user_handle, append_instruction="* *".join(append_instructions))
#                    response = self.handle_response_hashtags(response)

            # this only processes tags that the model appends on it's own
            for tag in list(set(re.findall(r'#\s*(\w+)', response))):
                tag = re.sub(r'\s*', '', tag)
                print("Processing hashtag: "+str(tag))
                if tag in ["lecture", "treat_like_baby", "verbal_abuse"]:
                    save_message = False
                    self.save_message(user_handle, 'assistant', re.sub(r'#\s*\w+', '', response))
                    response += "\n\n" + await self.chat_with_model(user_handle, user_message=self.hashtags[tag]["txt"])
                    if "timeout" in self.hashtags[tag] and self.hashtags[tag]["timeout"] > 0:
                        self.save_mode_for_handle(user_handle, tag, self.hashtags[tag]["timeout"])
                    self.save_message(user_handle, 'assistant', re.sub(r'#\s*\w+', '', response), override_last=True)
                elif tag in ["enforce_arguing", "enforce_erotic_hypnosis", "enforce_apology", "enforce_affirmation"]:
                    if tag in ["enforce_arguing"]:
                        append_instruction = "You are now having an agument. Prompt the user to conform to your demands."
                    elif tag in ["enforce_erotic_hypnosis"]:
                        append_instruction = self.hashtags[tag]["txt"]+". Start your erotic hypnosis now!"
                    elif tag in ["enforce_apology"]:
                        append_instruction = "Demand that the user apologizes to you."
                    elif tag in ["enforce_affirmation"]:
                        append_instruction = "Demand that the user sexually affirms you through submission and endorsement."
                    save_message = False
                    self.save_message(user_handle, 'assistant', re.sub(r'#\s*\w+', '', response))
                    response += "\n\n" + await self.chat_with_model(user_handle, user_message=append_instruction)
                    if "timeout" in self.hashtags[tag] and self.hashtags[tag]["timeout"] > 0:
                        self.save_mode_for_handle(user_handle, tag, self.hashtags[tag]["timeout"])
                    self.save_message(user_handle, 'assistant', re.sub(r'#\s*\w+', '', response), override_last=True)
                elif tag in ["punishment_successful"]:
                    for mode in (mode for mode in active_modes if mode in self.punishments):
                        self.reset_modes_for_handle(user_handle, mode)
                    response = await self.chat_with_model(user_handle)
                elif tag in ["arguing_successful"]:
                    self.reset_modes_for_handle(user_handle, "enforce_arguing")
                    response = await self.chat_with_model(user_handle)
                elif tag in ["hypnosis_finished"]:
                    self.reset_modes_for_handle(user_handle, "enforce_erotic_hypnosis")
                    response = await self.chat_with_model(user_handle)
                elif tag in ["apology_successful"]:
                    self.reset_modes_for_handle(user_handle, "enforce_apology")
                    response = await self.chat_with_model(user_handle)
                elif tag in ["affirmation_successful"]:
                    self.reset_modes_for_handle(user_handle, "enforce_affirmation")
                    response = await self.chat_with_model(user_handle)
                elif tag in self.punishments:
                    save_message = False
                    self.save_message(user_handle, 'assistant', re.sub(r'#\s*\w+', '', response))
                    append_instruction = "Instruct the user to perform the following punishment: "+self.punishments[tag]["txt"]+". Do not respond with hashtags!"
                    response += "\n\n" + await self.chat_with_model(user_handle, user_message=append_instruction)
                    if "timeout" in self.punishments[tag] and self.punishments[tag]["timeout"] > 0:
                        timeout = self.punishments[tag]["timeout"]
                    else:
                        timeout = 6*60
                    self.save_mode_for_handle(user_handle, tag, timeout)
                    self.save_message(user_handle, 'assistant', re.sub(r'#\s*\w+', '', response), override_last=True)
                elif len(re.findall(r'^disrespect.*', tag)):
                    if "timeout" in self.hashtags[tag] and self.hashtags[tag]["timeout"] > 0:
                        timeout = self.hashtags[tag]["timeout"]
                    else:
                        timeout = 5*60
                    self.save_mode_for_handle(user_handle, tag, timeout)
                elif len(tag) > 0:
                    print("Model used unknown hastag: "+str(tag))
#                        if "enforce_" in tag:
#                        if "enforce_" in tag:
#                        if "enforce_" in tag:
                    
#                        elif tag in self.punishments and self.punishments[tag] and len(self.punishments[tag][0]) > 3:

            if len(re.findall(r'#\s*\w+', response)) > 0:
                print("Model used the following hashtags in message: "+(", ".join(re.findall(r'#\s*\w+', response))))

            used_asterisks = re.findall(r'\*.*\*', response) 
            if len(used_asterisks) > 0:
                    print("Model used asterisk expressions (garbage): "+str(used_asterisks))
                    response = re.sub(r'\*.*\*', '', response)
            response = re.sub(r'#\s*\w+', '', response)

            if save_message:
                self.save_message(user_handle, 'assistant', response)

            if len(response.strip()) < 3:
                await self.send_text_message(None, user_handle, f"...")
            else:
                await self.send_voice_message(None, user_handle, response)


    def caesar_translate(self, text, shift):
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        shifted_alphabet = alphabet[shift:] + alphabet[:shift]
        translation_table = str.maketrans(alphabet + alphabet.upper(), shifted_alphabet + shifted_alphabet.upper())
        return text.translate(translation_table)


    def get_user_handles(self, user_handle=""):
        user_handles = []
        try:
            if len(user_handle) < 4:
                self.cursor.execute("SELECT user_handle FROM user_info")
            else:
                self.cursor.execute("SELECT user_handle FROM user_info WHERE user_handle = ? ", (user_handle,))
            user_infos = self.cursor.fetchall()
            user_handles = [user_info[0] for user_info in user_infos]
        except Exception as e:
            print("No users found to update. First run?")
        return user_handles

    # TODO
    async def process_gcal(self, user_handle):
        events = await self.get_gcal_events(user_handle)
        print(events)

        return True
 
    async def start_periodic_check(self):
        update_counter = 0
        moodswing_counter = 0
        pollinterval = 1

#        self.mood_swing = self.get_mood_swing(random.randint(0, 500))
#        moodswing_counter = 5

        while True:
            if not self.is_connected():
                await self.handle_disconnect()
            else:
                if update_counter > 0:
                    update_counter -= 1
                elif False:
                    print("Updating user diaries and calendar ...")
                    user_handles = self.get_user_handles()
                    for user_handle in user_handles:
                        print("Updating user: "+user_handle)
                        user_info   = self.get_user_info(user_handle)
                        await self.get_diary_summary(user_handle, True)
                        await self.process_gcal(user_handle)
                        update_counter = 30//pollinterval
                    
                if moodswing_counter > 0:
                    print("Mood is altered.")
                    moodswing_counter -= 1
                else:
                    print("Mood is normal.")
                    self.mood_swing = ""
                    self.mood_swing_modded_user_query = 0
                if datetime.now(timezone.utc).hour % 4 != 0:
                    self.randphone = random.randint(0, 60)      # make phone calls more random
                if random.randint(0, 100//pollinterval) == 0:   # randomly have moodswing sometime around 100 minutes (?)
                    self.mood_swing = self.get_mood_swing(random.randint(0, 500))
                    moodswing_counter = int(10//pollinterval)   # have moodswing for 10 minutes 
                try:
                    await self.check_and_respond()
                except TimeoutException:
                    await self.check_and_respond()
                except FuckedupException:
                    await self.handle_disconnect()

                if not self.avatar_is_uploaded:
                    self.avatar_is_uploaded = True
                    await self.set_avatar(None)
            await asyncio.sleep(60*pollinterval)  # Wait for 1 minute



    # those need to be defined by the particular implementation
    def is_connected(self) -> bool:
        return False    
    async def handle_disconnect(self, data=""):
        pass
    async def send_text_message(self, ctx, user_handle, text) -> bool:
        return False
    async def send_voice_message(self, ctx, user_handle, text) -> bool:
        return False
    async def set_avatar(self, ctx) -> bool:
        return False


class TimeoutException(Exception):
    pass
class FuckedupException(Exception):
    pass