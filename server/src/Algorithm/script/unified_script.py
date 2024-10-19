from transformers import AutoTokenizer, AutoModelForSequenceClassification
from nltk import word_tokenize, pos_tag, ne_chunk
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Optional, Union
from soynlp.normalizer import repeat_normalize
from datetime import datetime, timedelta
from konlpy.tag import Okt, Kkma
from konlpy.tag import Hannanum
from pykospacing import Spacing
from konlpy.tag import Komoran
from spacy.tokens import Span
import warnings
import calendar
import logging
import spacy
import torch
import pytz
import json
import nltk
import sys
import re
import io

nltk.download('punkt', )
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')

warnings.filterwarnings("ignore")

# 한국 표준시(KST) 타임존 설정
kst = pytz.timezone('Asia/Seoul')

hannanum = Hannanum()
komoran = Komoran()
spacing = Spacing()
kkma = Kkma()
okt = Okt()

# spaCy 모델 캐싱 (최초 한 번만 로드)
_cached_nlp = None

# 로그 설정 (파일로 기록하거나 콘솔로 출력)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_print():
    logging.info('정보성 메세지')
    logging.warning('경고성 메세지')
log_print()

# map_database 폴더 내의 stock_market.txt 파일을 읽어옴
stock_market_file = open(r'C:\Users\dlavk\SEBIN\AICC_TEAM\aicc_contest\aicc_map\map_database\stock_market\stock_market.txt', 'r', encoding='utf-8')
stock_market_news = stock_market_file.read()
stock_market_file.close()


# ================================================================================ Chatbot Entity Date Function ================================================================================
def convert_relative_years(match: str, time: bool = False) -> Optional[List[int]]:
    """
    입력된 문자열에서 상대적 또는 절대적 연도 표현이 포함되어 있을 때 해당 연도를 계산하여 반환

    Args:
        match (str): 상대적 또는 절대적 연도를 나타내는 문자열. 예: '3년 전', '2022년', '올해', '내년'
        time (bool): 미래 연도를 포함할지 여부, 기본값은 False

    Returns:
        List[Optional[int]]: 계산된 연도를 리스트로 반환. 예: ['2023'], ['2025']
    """
    today_year = datetime.now().year


    # 상대적 연도 표현을 포함한 경우 처리
    relative_years = {
        "재작년": today_year - 2,
        "작년": today_year - 1,
        "올해": today_year,
        "내년": today_year + 1 if time else None,
        "내휴냔": today_year + 2 if time else None
    }


    # match 안에 상대적 연도 표현이 포함되어 있을 때 해당 연도 처리
    for key, year_value in relative_years.items():
        if key in match:
            return [str(year_value)] if year_value is not None else None

    # '년 전', '년 후'와 절대 연도 표현을 한번에 처리
    year_shift = re.search(r'(\d{1,4})년\s?(전|후)?', match)

    if year_shift:
        year = int(year_shift.group(1))  # 숫자 추출
        shift = year_shift.group(2)      # '전' 또는 '후' 추출
        if shift == '전':
            calculated_year = today_year - year
        elif shift == '후':
            calculated_year = today_year + year
        else:
            calculated_year = year  # 절대 연도일 경우 그대로 반환

        if not time and calculated_year > today_year:
            return None  # 미래 연도를 포함하지 않도록 함
        return [calculated_year]

    return None


def convert_relative_months(match: str, time: bool = False, year: Optional[int] = None) -> List[str]:
    """
    입력된 문자열(match)에 포함된 상대적인 월 정보를 기준으로 실제 날짜(월)를 변환하는 함수.

    Args:
    - match (str): 상대적인 날짜 표현이 포함된 문자열 (예: '2분기', '3개월 전').
    - time (bool): True이면 미래 날짜를 그대로 반환하고, False이면 미래 날짜를 전년도 날짜로 변환.
    - year (int): 연도를 지정하는 선택적 인자. 지정하면 해당 연도의 날짜를 반환.

    Returns:
    - list[str]: 변환된 날짜들을 'YYYY-MM' 형식의 문자열 리스트로 반환.
    """

    today = datetime.now(kst).date()
    target_year = year if year else today.year
    specified_months = []

    match_exact_month = re.search(r'(\d{1,2})월(달)?', match)
    if match_exact_month:
        exact_month = int(match_exact_month.group(1))
        future_date = datetime(target_year, exact_month, 1).date()
        if year and future_date.year != year:
            return None if future_date > today and not time else [future_date.strftime("%Y-%m")]
        if not year and future_date > today and not time:
            future_date = future_date.replace(year=today.year - 1)
        return [future_date.strftime("%Y-%m")]
    match_month = re.search(r'(\d{1,2})개?월(?: (전|후))?', match)

    if match_month:
        months_offset = int(match_month.group(1))
        if '전' in match:
            past_date = today - relativedelta(months=months_offset)
            if year and past_date.year != year:
                return None if (past_date > today and not time) else [past_date.strftime("%Y-%m")]
            if not year and past_date > today and not time:
                past_date = past_date.replace(year=today.year - 1)
            return [past_date.strftime("%Y-%m")]

        if '후' in match:
            future_date = today + relativedelta(months=months_offset)
            if year and future_date.year != year:
                return None if (future_date > today and not time) else [future_date.strftime("%Y-%m")]
            return None if future_date > today and not time else [future_date.strftime("%Y-%m")]

        for i in range(months_offset):
            past_date = today - relativedelta(months=i)
            if year and past_date.year != year:
                return None if (past_date > today and not time) else specified_months.append(f"{past_date.year}-{past_date.month:02}")
            if not year and past_date > today and not time:
                past_date = past_date.replace(year=today.year - 1)
            specified_months.append(f"{past_date.year}-{past_date.month:02}")
        return sorted(specified_months)

    relative_months = {
        '다다음달': 2, '이번달': 0, '다음달': 1, '저저번달': -2, '저번달': -1,
        '연초': -today.month + 1,  # 1월까지의 거리
        '연말': 12 - today.month  # 12월까지의 거리
    }

    for key, offset in relative_months.items():
        if key in match:
            if key in ['다음달', '다다음달'] and not time:
                return None

            specified_month = (datetime(year if year else target_year, today.month, 1) + relativedelta(months=offset)).date()
            if specified_month > today and not time:
                specified_month -= relativedelta(years=1)
                if year is not None and specified_month.year != year:
                    return None

            return [specified_month.strftime("%Y-%m")]

    # 분기 표현 처리
    quarter_match = re.search(r'(\d)분기', match)
    if quarter_match:
        quarter = int(quarter_match.group(1))
        start_month, end_month, end_day = [(1, 3, 31), (4, 6, 30), (7, 9, 30), (10, 12, 31)][quarter - 1]
        start_date, end_date = datetime(target_year, start_month, 1).date(), datetime(target_year, end_month, end_day).date()

        if not year and not time:
            start_date, end_date = (start_date.replace(year=target_year - 1), end_date.replace(year=target_year - 1)) if today < start_date else (start_date, min(end_date, today))

        return [(start_date + relativedelta(months=i)).strftime("%Y-%m") for i in range((end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1)]

    return None

def convert_relative_weeks(match: str, time: bool = False, year: Optional[int] = None, month: Optional[int] = None) -> Union[List[str], None]:
    today = datetime.now().date()

    process_year = year if year else today.year
    process_month = [month] if month else []
    date_list = []

    for current_month in process_month or [today.month]:
        first_day_of_month = datetime(process_year, current_month, 1).date()
        last_day_of_month = (first_day_of_month + relativedelta(months=1)) - timedelta(days=1)
        start_of_week = today - timedelta(days=today.weekday())
        week_keys = ["첫째 주", "둘째 주", "셋째 주", "넷째 주", "마지막 주", "저저번 주", "지난 주", "이번 주", "다음 주", "다다음 주"]

        for week in week_keys:
            if week in match:
                if week == "첫째 주":
                    start_date = first_day_of_month
                    end_date = start_date + timedelta(days=(6 - start_date.weekday())) if start_date.weekday() != 6 else start_date
                elif week == "둘째 주":
                    start_date = first_day_of_month + timedelta(days=7 - first_day_of_month.weekday())
                    end_date = start_date + timedelta(days=6)
                elif week == "셋째 주":
                    start_date = first_day_of_month + timedelta(days=14 - first_day_of_month.weekday())
                    end_date = start_date + timedelta(days=6)
                elif week == "넷째 주":
                    start_date = first_day_of_month + timedelta(days=21 - first_day_of_month.weekday())
                    end_date = start_date + timedelta(days=6)
                elif week == "마지막 주":
                    end_date = last_day_of_month
                    start_date = end_date - timedelta(days=(end_date.weekday() + 1))
                elif week == "저저번 주":
                    start_date = start_of_week - timedelta(weeks=2)
                    end_date = start_date + timedelta(days=6)
                elif week == "지난 주":
                    start_date = start_of_week - timedelta(weeks=1)
                    end_date = start_date + timedelta(days=6)
                elif week == "이번 주":
                    start_date = start_of_week
                    end_date = start_of_week + timedelta(days=6)
                elif week == "다음 주":
                    start_date = start_of_week + timedelta(weeks=1)
                    end_date = start_date + timedelta(days=6)
                elif week == "다다음 주":
                    start_date = start_of_week + timedelta(weeks=2)
                    end_date = start_date + timedelta(days=6)

                current_date = start_date

                while current_date <= end_date:
                    if time:
                        date_list.append(current_date.strftime('%Y-%m-%d'))
                    else:
                        if week in ["다음 주", "다다음 주"]:
                            return None

                        if end_date <= today:
                            date_list.append(current_date.strftime('%Y-%m-%d'))
                        elif current_date > today:
                            start_date -= relativedelta(months=1)
                            end_date -= relativedelta(months=1)
                            current_date = start_date

                            while current_date <= end_date:
                                if current_date <= today:
                                    date_list.append(current_date.strftime('%Y-%m-%d'))
                                current_date += timedelta(days=1)
                            break
                        elif current_date <= today and today <= end_date:
                            while current_date <= today:
                                date_list.append(current_date.strftime('%Y-%m-%d'))
                                current_date += timedelta(days=1)
                            break
                    current_date += timedelta(days=1)

    if date_list:
        date_list = sorted(date_list)
        first_date = datetime.strptime(date_list[0], '%Y-%m-%d').date()
        last_date = datetime.strptime(date_list[-1], '%Y-%m-%d').date()

        if (year is not None and first_date.year != year) or (month is not None and first_date.month != month):
            return None

    return date_list


def convert_relative_days(match: str, time: bool = False, year: Optional[int] = None, month: Optional[int] = None, week: Optional[List[str]] = None) -> Optional[List[str]]:
    """
    입력된 날짜 표현을 분석하여 실제 날짜로 변환하는 함수.
    """
    today = datetime.now().date()

    # 특정 날짜가 입력이 안되면 default를 올해, 이번 달, 이번 주로 설정
    processed_year = int(year) if year else today.year
    processed_month = int(month) if month else today.month

    processed_week = [today - timedelta(days=today.weekday()) + timedelta(days=i) for i in range(7)]

    if '보름' in match:
        # 연도와 월 설정
        target_year = year if year else today.year
        target_months = [month] if month else ([today.month] if not year else range(1, 13))

        # 각 월의 15일을 계산하고, 미래 날짜 처리
        dates = [datetime(target_year, m, 15).date() for m in target_months]
        dates = [d for d in dates if time or d <= today]

        return [d.strftime('%Y-%m-%d') for d in dates] if dates else None


    # 기존의 'N일 전', 'N일 후', 'N일' 형태의 날짜 처리
    relative_day_pattern = re.search(r'(\d+)일(?: (전|후))?', match)
    if relative_day_pattern:
        days = int(relative_day_pattern.group(1))
        direction = relative_day_pattern.group(2).strip() if relative_day_pattern.group(2) else None
        # 날짜 계산 로직
        if direction == '전':
            target_date = today - timedelta(days=days)
        elif direction == '후':
            target_date = today + timedelta(days=days)
        else:
            # 일(day)만 주어진 경우
            input_day = days
            input_month = processed_month
            target_year = processed_year

            while True:
                try:
                    target_date = datetime(target_year, input_month, input_day).date()
                    break  # 날짜 생성에 성공하면 루프 탈출
                except ValueError:
                    # 날짜가 유효하지 않을 경우 월이나 연도를 조정
                    if input_month > 1:
                        input_month -= 1
                    else:
                        input_month = 12
                        target_year -= 1
                    # 만약 너무 오래 반복하면 None 반환
                    if target_year < 2000:  # 임의의 기준 연도 설정
                        return None

            # 미래 날짜를 시간 플래그에 따라 조정
            if not time and target_date > today:
                if not year and month:
                    target_year -= 1
                    try:
                        target_date = datetime(target_year, input_month, input_day).date()
                    except ValueError:
                        return None

        return [target_date.strftime('%Y-%m-%d')] if target_date else None

    # '평일', '주말' 또는 특정 요일 처리
    days_ahead = {'월요일': 0, '화요일': 1, '수요일': 2,
                    '목요일': 3, '금요일': 4, '토요일': 5, '일요일': 6, '평일': 7, '주말': 8}

    if any(weekday in match for weekday in days_ahead):
        def filter_dates(dates, is_weekday):
            # 평일 또는 주말 필터링, 미래 날짜는 time이 False일 때만 제거
            filtered = [date for date in dates if (date.weekday() < 5) == is_weekday and (time or date <= today)]
            return [date.strftime('%Y-%m-%d') for date in filtered] or None

        # 1. 주어진 주의 날짜들이 있는 경우 (week 인자가 주어짐)
        if week:
            dates = [datetime.strptime(date, '%Y-%m-%d').date() for date in week]

        # 2. 연도만 주어진 경우 (year는 있고, month는 없는 경우)
        elif year and not month:
            for weekday, idx in days_ahead.items():
                if weekday in match:
                    first = datetime(processed_year, 1, 1).date()
                    first += timedelta(days=(idx - first.weekday() + 7) % 7)
                    last = datetime(processed_year, 12, 31).date()
                    return [first.strftime('%Y-%m-%d')] + [(first + timedelta(weeks=i)).strftime('%Y-%m-%d')
                                                          for i in range(1, (last - first).days // 7 + 1)
                                                            if time or first + timedelta(weeks=i) <= today]

        # 3. 연도와 월이 모두 주어진 경우 (year와 month가 모두 있음)
        elif year and month:
            start_of_month = datetime(processed_year, processed_month, 1).date()
            end_of_month = (start_of_month + relativedelta(months=1)) - timedelta(days=1)
            dates = [start_of_month + timedelta(days=i) for i in range((end_of_month - start_of_month).days + 1)]

        # 4. 월만 주어진 경우 (year가 없고 month만 있는 경우)
        elif month:
            start_of_month = datetime(today.year, month, 1).date()
            end_of_month = (start_of_month + relativedelta(months=1)) - timedelta(days=1)
            dates = [start_of_month + timedelta(days=i) for i in range((end_of_month - start_of_month).days + 1)]

        # 5. 아무런 정보가 주어지지 않은 경우: 이번 주의 날짜 조회
        else:
            start_of_week = today - timedelta(days=today.weekday())
            dates = [start_of_week + timedelta(days=i) for i in range(7)]

        # 결과 생성
        if '평일' in match:
            result = filter_dates(dates, is_weekday=True)
        elif '주말' in match:
            result = filter_dates(dates, is_weekday=False)
        else:
            # 특정 요일에 해당하는 모든 날짜 추출
            matching_weekdays = []
            for weekday in days_ahead:
                if weekday in match:
                    weekday_index = days_ahead[weekday]
                    matching_dates = [date.strftime('%Y-%m-%d') for date in dates if date.weekday() == weekday_index and (time or date <= today)]
                    matching_weekdays.extend(matching_dates)
            result = matching_weekdays or None

        return result

    # 월별 기간 표현 처리: "월초", "중순", "월말"
    if any(period in match for period in ['월초', '중순', '월말']):
        target_month = datetime(processed_year, processed_month, 1).date()

        periods = {
            '월초': (0, 9),
            '중순': (10, 19),
            '월말': (20, (target_month + relativedelta(months=1) - timedelta(days=1)).day)
        }
        start_offset, end_offset = next((s, e) for p, (s, e) in periods.items() if p in match)
        start_of_period = target_month + timedelta(days=start_offset)
        end_of_period = target_month + timedelta(days=end_offset) if '월말' not in match else (target_month + relativedelta(months=1) - timedelta(days=1))

        if not time and start_of_period > today:
            if not month:
                start_of_period -= relativedelta(months=1)
                end_of_period -= relativedelta(months=1)
            elif not year:
                start_of_period -= relativedelta(years=1)
                end_of_period -= relativedelta(years=1)

        # 미래 데이터 처리
        if not time and start_of_period <= today < end_of_period:
            end_of_period = min(end_of_period, today)

        # 모든 날짜 생성
        all_dates = [(start_of_period + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((end_of_period - start_of_period).days + 1)]
        return all_dates

    # 표현을 못 찾음
    return None

def convert_date_expression(text: str, time: bool=False) -> Optional[List[str]]:
    """
    주어진 텍스트에서 날짜 표현을 찾아 실제 날짜로 변환합니다.

    Args:
    - text (str): 입력 텍스트

    Returns:
    - list: 변환된 날짜 리스트 (문자열 형식 'YYYY-MM-DD')
    """
    today = datetime.now().date()  # 현재 날짜 설정
    date_expressions = ['오늘', '내일', '모레', '글피', '어제', '엊그제', '최근']
    converted_dates = []

    # 날짜 표현이 텍스트에 포함되어 있는지 확인하고 변환
    for expr in date_expressions:
        if expr in text:
            if expr == '오늘':
                converted_dates.append(today.strftime('%Y-%m-%d'))
            elif expr == '내일':
                if time:
                    converted_dates.append((today + timedelta(days=1)).strftime('%Y-%m-%d'))
                else:
                    return  None
            elif expr == '모레':
                if time:
                    converted_dates.append((today + timedelta(days=2)).strftime('%Y-%m-%d'))
                else:
                    return None
            elif expr == '글피':
                if time:
                    converted_dates.append((today + timedelta(days=3)).strftime('%Y-%m-%d'))
                else:
                    return None
            elif expr == '어제':
                converted_dates.append((today - timedelta(days=1)).strftime('%Y-%m-%d'))
            elif expr == '엊그제':
                converted_dates.append((today - timedelta(days=2)).strftime('%Y-%m-%d'))
            elif expr == '최근':
                # 최근 7일 계산
                converted_dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
            return converted_dates

    return None


# 각 패턴 그룹 정의
date_patterns: Dict[str, Dict[str, List[str]]] = {
    "상대적 날짜": {
        "최근": [r"\b최근|요즘|근래|최신\b"],
        "오늘": [r'\b오늘|금일|지금\b'],
        "내일": [r'\b내일|익일\b'],
        "모레": [r'\b모레|내일모레|모래\b'],
        "글피": [r'\b글피\b'],
        "어제": [r'\b어제|어저께|작일\b'],
        "엊그제": [r'\b엊그제|엊그저께|그제|그저께\b']
    },
    "상대적 연도": {
        "재작년": [r'\b재작년\b'],
        "작년": [r'\b작년\b'],
        "내년": [r'\b내년\b'],
        "올해": [r'\b올해|현재 연도\b'],
        "내휴냔": [r'\b내후년|내휴냔\b']
    },
    "상대적 월": {
        "11월": [r'\b11월\b'],
        "12월": [r'\b12월\b'],
        "1월": [r'\b1월\b'],
        "2월": [r'\b2월\b'],
        "3월": [r'\b3월\b'],
        "4월": [r'\b4월\b'],
        "5월": [r'\b5월\b'],
        "6월": [r'\b6월\b'],
        "7월": [r'\b7월\b'],
        "8월": [r'\b8월\b'],
        "9월": [r'\b9월\b'],
        "10월": [r'\b10월\b'],
        "다다음달": [r'\b다다음달\b'],
        "저저번달": [r'\b저저번달\b'],
        "다음달": [r'\b다음 달|다음달\b'],
        "저번달": [r'\b저번 달|지난 달|저번달|지난달\b'],
        "이번달": [r'\b이번달|이번 달|금월\b'],
        "연말": [r'\b연말\b'],
        "연초": [r'\b연초\b']
    },
    "주 관련 상대적 날짜": {
        "첫째 주": [r'\b첫째 주|첫쨰 주|첫째주|첫쨰주|첫쨰 주|첫번째 주|첫주|1주차'],
        "둘째 주": [r'\b둘째주|둘쨰주|둘쨰 주|둘째 주|두째주|두번째 주|2주차|두째 주'],
        "셋째 주": [r'\b셋째주|세번째 주|3주차|셋째 주'],
        "넷째 주": [r'\b넷째주|네번째 주|4주차'],
        "저저번 주": [r'\b저저번주\b'],
        "다다음 주": [r'\b다다음주\b'],
        "마지막 주": [r'\b마지막|다섯번째 주|마지막 주|5주차|다섯째 주'],
        "지난 주": [r'\b지난주|저번주|지난 주|저번 주\b'],
        "이번 주": [r'\b이번주|이번 주\b'],
        "다음 주": [r'\b다음주|다음 주\b']
    },
    "요일": {
        "월요일": [r'\b월요일\b'],
        "화요일": [r'\b화요일\b'],
        "수요일": [r'\b수요일\b'],
        "목요일": [r'\b목요일\b'],
        "금요일": [r'\b금요일\b'],
        "토요일": [r'\b토요일\b'],
        "일요일": [r'\b일요일\b'],
        "평일": [r'\b평일|평일에\b'],
        "주말": [r'\b주말|주말에\b'],
        "중순": [r'\b중순\b'],
        "보름": [r'\b보름\b'],
        "월말": [r'\b월말\b'],
        "월초": [r'\b월초\b']
    }
}

def replace_with_pattern_keys(text: str) -> str:
    """
    텍스트에서 날짜 표현을 해당 키로 치환합니다.

    Args:
    - text (str): 입력 텍스트

    Returns:
    - str: 변환된 텍스트
    """
    # 패턴 그룹을 순회하며, 매칭되는 부분을 키로 치환
    for group_name, patterns in date_patterns.items():
        for key, regex_list in patterns.items():
            for regex in regex_list:
                text = re.sub(regex, key, text)

    return text

def extract_date_info(text, time=False):
    """
    주어진 텍스트에서 날짜 정보를 추출하여 실제 날짜로 변환합니다.

    Args:
    - text (str): 입력 텍스트
    - time (bool): 미래 날짜를 포함할지 여부를 결정하는 플래그

    Returns:
    - list: 변환된 날짜 리스트 (문자열 형식 'YYYY-MM-DD')
    """

    # 텍스트 패턴 치환 진행
    text = replace_with_pattern_keys(text)

    # convert_date_expression으로부터 변환된 날짜가 있으면 반환
    converted_dates = convert_date_expression(text, time=time)

    # 미래 날짜 표현에 대해서만 time=False일 경우 None 반환
    future_expressions = ['내일', '모레', '글피', '다음달', '내년', '내후년']
    if not time and any(expr in text for expr in future_expressions):
        return None

    if converted_dates:
        return converted_dates

    year, month, month_result, week, result = None, None, None, None, None

    # 상대적 연도, 월, 주, 요일 패턴 목록
    year_patterns = [pattern for sublist in date_patterns['상대적 연도'].values() for pattern in sublist]
    month_patterns = [pattern for sublist in date_patterns['상대적 월'].values() for pattern in sublist]
    week_patterns = [pattern for sublist in date_patterns['주 관련 상대적 날짜'].values() for pattern in sublist]
    day_patterns = [pattern for sublist in date_patterns['요일'].values() for pattern in sublist]

    patterns_to_check = {
        "year": (year_patterns + [r'\b(\d{2,4}년)\b'], convert_relative_years, {'time': time}),
        "month": (month_patterns + [r'\b(\d{1,2})월(달|만)?\b', r'\b(\d{1,2}개월)\b', r'\b\d{1}분기\b'], convert_relative_months, {'time': time, 'year': year}),
        "week": (week_patterns, convert_relative_weeks, {'time': time, 'year': year, 'month': month}),
        "day": (day_patterns + [r'\b(\d{1,2})일\b'], convert_relative_days, {'time': time, 'year': year, 'month': month, 'week': week})
    }

    # 패턴을 순회하며 일치하는 것을 변환
    for key, (patterns, convert_function, kwargs) in patterns_to_check.items():
        for pattern in patterns:
            if re.search(pattern, text):
                if key == "year" and convert_function:
                    year_result = convert_function(text, **kwargs)
                    if year_result:
                        year = int(year_result[0])
                        patterns_to_check["month"][2]['year'] = year
                elif key == "month" and convert_function:
                    month_result = convert_function(text, **patterns_to_check["month"][2])
                    if month_result:
                        month = month_result
                elif key == "week":
                    # year와 month가 None일 때는 None으로 전달
                    kwargs['year'] = year
                    kwargs['month'] = int(month[0].split('-')[1]) if month else None
                    week = convert_function(text, **kwargs)
                    result = week
                elif key == "day":
                    kwargs['year'] = year
                    kwargs['month'] = int(month[0].split('-')[1]) if month else None
                    kwargs['week'] = week
                    result = convert_function(text, **kwargs)
                break


    final_result = result or week or month_result or ([str(year)] if year else None)

    if not (final_result and final_result[0]) or (
        not time and (any(expr in text for expr in future_expressions))):
        return None

    date_str = final_result[0]
    final_date = datetime.strptime(date_str, '%Y' if len(date_str) == 4 else '%Y-%m' if len(date_str) == 7 else '%Y-%m-%d').date()

    return None if not time and final_date > datetime.now().date() else final_result

def check_conjunction_and_particle_with_kkma(text: str) -> bool:
    """
    텍스트에서 특정 조사나 접속사가 포함되어 있는지 확인합니다.

    Args:
    - text (str): 입력 텍스트

    Returns:
    - bool: 조건에 맞는 조사나 접속사가 포함되어 있으면 True, 그렇지 않으면 False
    """
    # KKMA로 품사 태깅된 리스트
    kkma_tagged = kkma.pos(text)

    # 형태소를 하나로 결합하여 원래의 단어를 복원
    combined_text = ''.join([word for word, pos in kkma_tagged])

    # 타겟 조사 및 접속사 집합
    target_words = {'과', '이랑', '그리고', '에서', '부터', '까지', '와', '별', '마다'}

    # 결합된 형태소들이 '와'로 해석될 수 있는지 확인
    if combined_text in target_words:
        return True

    # 분리된 형태소가 '오'와 '아'로 나온 경우 '와'로 결합하여 처리
    if ('오', 'VA') in kkma_tagged and ('아', 'ECS') in kkma_tagged:
        return True

    # 유효한 품사 태그 집합
    valid_tags = {'XSN', 'VA', 'ECS', 'VV', 'MAC', 'JKS', 'JC', 'JKC', 'JKG', 'JKO', 'JKB', 'JKV', 'JKQ', 'JX', 'JKM', 'MAJ', 'NNB', 'NNG'}

    # 태그된 텍스트에서 조건 확인
    for word, pos in kkma_tagged:
        if word in target_words and pos in valid_tags:
            return True

    return False

def get_all_dates_between(start_date_str, end_date_str, time=False):
    """
    주어진 두 날짜 사이의 모든 날짜를 반환합니다.

    Args:
    - start_date_str (str): 시작 날짜 문자열 (YYYY, YYYY-MM, YYYY-MM-DD 형식 가능)
    - end_date_str (str): 종료 날짜 문자열 (YYYY, YYYY-MM, YYYY-MM-DD 형식 가능)
    - time (bool): True면 미래 날짜 포함, False면 현재 날짜까지만 포함

    Returns:
    - list: 두 날짜 사이의 모든 날짜 목록
    """
    today = datetime.now().date()

    def parse_date(date_str, is_start=True):
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                date = datetime.strptime(date_str.strip(), fmt)
                if fmt == "%Y":
                    return date.replace(month=1, day=1) if is_start else date.replace(month=12, day=31)
                elif fmt == "%Y-%m":
                    return date.replace(day=1) if is_start else (date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                return date
            except ValueError:
                continue
        return None

    # 시작 날짜와 종료 날짜 파싱
    start_date, end_date = parse_date(start_date_str, True), parse_date(end_date_str, False)

    if not start_date or not end_date:
        return None

    # 시작 날짜와 종료 날짜 사이의 모든 날짜 생성
    return [(start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range((end_date - start_date).days + 1)
            if time or (start_date + timedelta(days=i)).date() <= today]

def split_and_return_periods(text: str, time: bool = False) -> List[str]:
    today = datetime.now().date()

    weekday_map = {"월요일": 0, "화요일": 1, "수요일": 2, "목요일": 3, "금요일": 4, "토요일": 5, "일요일": 6}

    # 정규식 패턴 정의
    patterns = {
        'range': r"(.*?)\s*(에서|부터)\s*(.*)",
        'conjunction': r"(\S+)\s?(과|이랑|그리고|와)\s?(\S+)",
        'until': r"(.*?)\s*(까지)",
        'frequency': r"(월요일|화요일|수요일|목요일|금요일|토요일|일요일|평일|주말)?\s*(별|마다)",
        'unit': r"\s*(일|주|월|분기|년|연도)"
    }

    # match_4: "요일마다", "평일마다", "주말마다", "별", "마다"
    freq_match = re.search(patterns['frequency'], text)

    if freq_match and check_conjunction_and_particle_with_kkma(freq_match.group(2)):
        period_type, freq = freq_match.groups()

        if period_type in weekday_map:
            target_weekday = weekday_map[period_type]
            return sorted([
                (today - timedelta(days=i)).strftime('%Y-%m-%d')
                for i in range(1, 30) if (today - timedelta(days=i)).weekday() == target_weekday
            ][:3])
        elif period_type in ["평일", "주말"]:
            date_list, weeks = [], 0
            while weeks < 3:
                week_start = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks)
                if period_type == "평일":
                    date_list += [(week_start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(5)]
                else:
                    date_list += [(week_start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(5, 7)]
                weeks += 1
            return sorted(set(date_list))
        else:
            unit_match = re.search(patterns['unit'], text)
            unit = unit_match.group(1) if unit_match else None

            if unit == "일":
                return [ (today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7) ]
            elif unit == "주":
                return sorted({ (today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(21) })
            elif unit == "월":
                return sorted({ f"{(today - relativedelta(months=i)).year}-{(today - relativedelta(months=i)).month:02d}" for i in range(3) })
            elif unit == "분기":
                return sorted({ f"{(today - relativedelta(months=i)).year}-{(today - relativedelta(months=i)).month:02d}" for i in range(12) })
            elif unit in ["년", "연도"]:
                return sorted({ f"{today.year - i}" for i in range(3) })

    # match_1: "에서", "부터"
    range_match = re.search(patterns['range'], text)

    if range_match and check_conjunction_and_particle_with_kkma(range_match.group(2)):
        start_dates = extract_date_info(range_match.group(1).strip(), time)
        end_dates = extract_date_info(range_match.group(3).strip(), time)

        if start_dates and end_dates:
            all_dates = sorted(get_all_dates_between(start_dates[0], end_dates[-1], time))
            return all_dates
        return start_dates or end_dates or None

    # match_2: "과", "이랑", "그리고", "와"
    conj_match = re.search(patterns['conjunction'], text)

    if conj_match and check_conjunction_and_particle_with_kkma(conj_match.group(2)):
        before, _, after = conj_match.groups()
        start_dates = extract_date_info(before.strip(), time)
        end_dates = extract_date_info(after.strip(), time)
        date = sorted(set(start_dates or []) | set(end_dates or []))
        return date if date else None

    # match_3: "까지"
    until_match = re.search(patterns['until'], text)

    if until_match and check_conjunction_and_particle_with_kkma(until_match.group(2)):
        final_dates = extract_date_info(until_match.group(1).strip(), time)
        result = []

        for d in final_dates:
            try:
                final_dt = datetime.strptime(d, "%Y-%m-%d").date()
            except ValueError:
                try:
                    final_dt = datetime.strptime(d, "%Y-%m").date().replace(day=calendar.monthrange(datetime.strptime(d, "%Y-%m").year, datetime.strptime(d, "%Y-%m").month)[1])
                except ValueError:
                    try:
                        final_dt = datetime.strptime(d, "%Y").date().replace(month=12, day=31)
                    except ValueError:
                        continue

        unit_mapping = {'일': 7, '주': 21, '월': 3, '년': 3}
        unit = next((u for u in unit_mapping if u in text), '일')
        days_delta = unit_mapping[unit]

        start = final_dt - (timedelta(days=days_delta) if unit == '주'
                            else relativedelta(months=days_delta) if unit == '월'
                            else relativedelta(years=days_delta) if unit == '년'
                            else timedelta(days=days_delta))

        return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, (final_dt - start).days + 1)]


    # 기본 날짜 추출
    try:
        result = sorted(extract_date_info(text, time))
        return result
    except Exception as e:
        return None


# ================================================================================ Entity Stock Function ================================================================================
def get_spacy_model():
    global _cached_nlp
    if _cached_nlp is None:
        _cached_nlp = spacy.load("ko_core_news_sm", disable=["parser", "tagger", "textcat"])
        Span.set_extension("cleaned_text", default=None, force=True)
    return _cached_nlp

def extract_stock_entities(text):
    # 주식 관련 패턴 정의
    patterns = {
        "삼성전자": r"삼성전자|삼성|삼전|samsung",
        "애플": r"애플|apple",
        "비트코인": r"비트코인|bitcoin|비트|코인|coin",
        "PER": r"PER|주가수익비율|Price Earning Ratio|per",
        "PBR": r"PBR|주가순자산비율|Price Book-value Ratio|pbr",
        "ROE": r"ROE|자기자본이익률|Return on Equity|roe",
        "MC": r"시총|총액|MC|시가총액|Market Cap|mc"
    }

    # 조사 및 종결어미 제거
    def clean_text(text):
        return re.sub(r'(과|와|의|가|이|을|를|은|는|에서|으로|고|까지|부터|도|만|조차|뿐|에|와|에서|로|이다|입니다|해요|하겠습니다)$', '', text)

    # 사용자 정의 spaCy 파이프라인 컴포넌트
    @spacy.Language.component("custom_stock_entity_adder")
    def custom_stock_entity_adder(doc):
        new_ents = []
        for token in doc:
            noun_phrase = clean_text(token.text)
            for label, pattern in patterns.items():
                if re.search(pattern, noun_phrase):
                    new_ent = Span(doc, token.i, token.i + 1, label=label)
                    new_ent._.set("cleaned_text", noun_phrase)
                    new_ents.append(new_ent)
                    break
        doc.ents = new_ents
        return doc

    # spaCy 모델 로드 (캐싱된 모델 사용)
    nlp = get_spacy_model()
    if "custom_stock_entity_adder" not in nlp.pipe_names:
        nlp.add_pipe("custom_stock_entity_adder", after="ner")

    doc = nlp(text)
    entities = [(ent._.get("cleaned_text"), ent.label_) for ent in doc.ents]
    return entities

def stock_information(text):
    entities = extract_stock_entities(text)
    entity_labels = {label for _, label in entities}

    stock_labels = {"삼성전자", "애플", "비트코인"}
    info_labels = {"PBR", "PER", "ROE", "MC"}

    requested_stocks = stock_labels.intersection(entity_labels)
    requested_infos = info_labels.intersection(entity_labels)

    if requested_stocks and requested_infos:
        stock = next(iter(requested_stocks))
        info = next(iter(requested_infos))
        date = "2024-09-01"
        query = f"MPPRSELECT {get_stock_column(stock, info)} FROM tb_stock WHERE fd_date = '{date}';"
        return query
    return ''

def get_stock_column(stock, info):
    stock_column_map = {
        "삼성전자": {"PBR": "sc_ss_pbr", "PER": "sc_ss_per", "ROE": "sc_ss_roe", "MC": "sc_ss_mc"},
        "애플": {"PBR": "sc_ap_pbr", "PER": "sc_ap_per", "ROE": "sc_ap_roe", "MC": "sc_ap_mc"}
    }
    return stock_column_map.get(stock, {}).get(info, '')




# ================================================================================ Make Query Function ================================================================================
# 소비, 수입, 입출금 등을 위한 패턴
def process_date_format(input_date=None, date_type="%Y-%m-%d"):
    """
    주어진 날짜 형식(input_date)에 맞춰 SQL 쿼리 문자열을 생성하는 함수.
    'yyyy-mm-dd', 'yyyy-mm', 'yyyy' 형식의 날짜를 처리하며, 날짜 형식에 따라 다른 쿼리 형식을 반환한다.

    Args:
    input_date (list): 날짜 정보가 포함된 리스트. 'yyyy-mm-dd', 'yyyy-mm', 또는 'yyyy' 형식.
    date_type (str): 날짜의 포맷. 기본값은 "%Y-%m-%d"이며, input_date가 없을 경우 오늘 날짜로 설정할 때 사용됨.

    Returns:
    str: SQL 쿼리 형식의 문자열.
    """
    
    # input_date가 None이거나 빈 리스트인 경우 오늘 날짜로 설정
    if not input_date:
        date_query = ""
        return date_query
        # input_date = [datetime.strftime(datetime.today(), date_type)]
    
    # 날짜 형식에 따른 처리
    first_date = input_date[0]

    if len(first_date) == 10:  # 형식이 'yyyy-mm-dd'
        date_query = "AND rp_date IN ("
        date_query += ", ".join(f'"{date}"' for date in input_date)
        date_query += ")"
        return date_query

    elif len(first_date) == 7:  # 형식이 'yyyy-mm'
        date_query = "AND (" + " OR ".join(f'rp_date LIKE "{date}%"' for date in input_date) + ")"
        return date_query

    elif len(first_date) == 4:  # 형식이 'yyyy'
        date_query = "AND (" + " OR ".join(f'rp_date LIKE "{date}%"' for date in input_date) + ")"
        return date_query

    else:
        today_date = datetime.strftime(datetime.today(), date_type)
        date_query = f'AND rp_date LIKE "{today_date}%"'
        return date_query
    
# 주식 수량을 위한 패턴
def process_date_format_stock_qty(input_date, date_type='%Y-%m-%d'):
    if input_date == None:
        input_date = [datetime.strftime(datetime.today(), date_type)]  # 오늘

    if len(input_date[0]) == 10:  # 형식이 'yyyy-mm-dd'
        date_query = f"AND sh_date <= '{input_date[0]}'"
        return date_query

    elif len(input_date[0]) == 7:  # 형식이 'yyyy-mm'
        year, month = map(int, input_date[0].split('-'))
        last_day = calendar.monthrange(year, month)[1]  # 그 달의 마지막 날 계산
        end_date = datetime(year, month, last_day).strftime('%Y-%m-%d')  # 그 달의 마지막 날
        date_query = f"AND sh_date <= '{end_date}'"
        return date_query

    elif len(input_date[0]) == 4:  # 형식이 'yyyy'
        year = int(input_date[0])
        end_date = datetime(year, 12, 31).strftime('%Y-%m-%d')  # 그 해의 12월 31일
        date_query = f"AND sh_date <= '{end_date}'"
        return date_query
    else:
        end_date = datetime.strftime(datetime.today(), date_type)
        date_query = f"AND sh_date <= '{end_date}'"
        return date_query

def generate_query_expend(ent1, rp_part, add_query, date_query, query_type):
    # 기본 쿼리 템플릿
    base_query = (
        "SELECT rp_date, rp_detail, rp_amount "
        "FROM tb_received_paid "
        "WHERE user_id = {{user_id}} AND rp_part = {rp_part} {add_query} {date_query} "
    ).format(rp_part=rp_part, add_query=add_query, date_query=date_query)

    # 'frequent' 타입은 특별한 쿼리 구조를 가짐
    if query_type == 'frequent':
        frequent_query = (
            "AND rp_detail IN ("
            "SELECT rp_detail FROM tb_received_paid "
            "WHERE user_id = {{user_id}} AND rp_part = {rp_part} {add_query} {date_query} "
            "GROUP BY rp_detail HAVING COUNT(*) >= 3 ORDER BY COUNT(*) DESC"
            ") "
            "ORDER BY rp_detail DESC, rp_amount LIMIT 3;"
        ).format(rp_part=rp_part, add_query=add_query, date_query=date_query)
        return base_query + frequent_query

    # 쿼리 타입에 따른 ORDER BY 절과 LIMIT 값을 매핑
    query_mapping = {
        'highest': {'order_by': 'rp_amount DESC', 'limit': 1},
        'top5': {'order_by': 'rp_amount DESC', 'limit': 5},
        'lowest': {'order_by': 'rp_amount ASC', 'limit': 1},
        'bottom5': {'order_by': 'rp_amount ASC', 'limit': 5},
    }

    # 매핑된 쿼리 타입 처리
    if query_type in query_mapping:
        order_by = query_mapping[query_type]['order_by']
        limit = query_mapping[query_type]['limit']
        return base_query + f"ORDER BY {order_by} LIMIT {limit}"

    return None

def generate_query_TRANSACTION(detail, add_query, date_query, order_by=None, limit=None, frequent=False):
    base_query = f'SELECT rp_date, rp_detail, rp_amount FROM tb_received_paid WHERE user_id = {{user_id}} AND rp_detail = "{detail}" {add_query} {date_query}'
    if frequent:
        # 자주 발생한 데이터를 찾기 위한 추가 쿼리
        base_query = f'SELECT rp_detail, COUNT(*) as freq, SUM(rp_amount) as Total_amount FROM tb_received_paid WHERE user_id = {{user_id}} AND rp_detail = "{detail}" {add_query} {date_query} GROUP BY rp_detail HAVING COUNT(*) >= 3'
    if order_by:
        base_query += f' ORDER BY rp_amount {order_by}'
    if limit:
        base_query += f' LIMIT {limit}'
    return base_query

def finance_pattern_query(finance_query, input_time=None, entity1=None, entity2=None, date_query=None, text=None):
    
    query = {}
    no_space_text = text.replace(" ", "")
    add_query = "AND rp_hold = 0" if "고정" in no_space_text else ""
    add_str = "고정" if add_query else ""

    if finance_query == "지출" or finance_query == "소득" or r'구매|구입|\b산\b' in no_space_text:
        for ent1 in entity1:
            for ent2 in entity2:

                # "지출" 또는 "소득"으로 직접 설정
                finance_type = "지출" if finance_query == "지출" else "소득"

                if ent2[1] == "sum":
                    rp_part = 1 if finance_query == "지출" or r'구매|구입|\b산\b' in no_space_text else 0
                    query[f'{add_str}{finance_type}_sum'] = f'SELECT SUM(rp_amount) as Total_amount FROM tb_received_paid WHERE user_id = {{user_id}} AND rp_part = {rp_part} {add_query} ' + date_query
                
                elif ent2[1] == "average":
                    rp_part = 1 if finance_query == "지출" or r'구매|구입|\b산\b' in no_space_text else 0
                    query[f'{add_str}{finance_type}_avg'] = f'SELECT AVG(rp_amount) as Average_amount FROM tb_received_paid WHERE user_id = {{user_id}} AND rp_part = {rp_part} {add_query} ' + date_query
                
                elif ent2[1] == "sort":
                    rp_part = 1 if finance_query == "지출" or r'구매|구입|\b산\b' in no_space_text else 0
                    if any(word in no_space_text for word in ["큰", "크게", "높은", "높게"]):
                        if any(word in no_space_text for word in ["가장", "최고", "제일"]):
                            query[f'{add_str}{finance_type}_highest'] = generate_query_expend(ent1, rp_part, add_query, date_query, 'highest')
                        else:
                            query[f'{add_str}{finance_type}_top5'] = generate_query_expend(ent1, rp_part, add_query, date_query, 'top5')
                    
                    elif any(word in no_space_text for word in ["작은", "적게", "낮은", "낮게", "적은", "작게"]):
                        if any(word in no_space_text for word in ["가장", "최고", "제일"]):
                            query[f'{add_str}{finance_type}_lowest'] = generate_query_expend(ent1, rp_part, add_query, date_query, 'lowest')
                        else:
                            query[f'{add_str}{finance_type}_bottom5'] = generate_query_expend(ent1, rp_part, add_query, date_query, 'bottom5')
                    
                    elif any(word in no_space_text for word in ["자주", "많이", "빈번", "반복", "주요", "많은"]):
                        query[f'{add_str}{finance_type}_frequent'] = generate_query_expend(ent1, rp_part, add_query, date_query, 'frequent')

                elif ent2[1] == "simple":  # None일 때 sum, average, sort 조건 제외한 쿼리만 추가
                    rp_part = 1 if finance_query == "지출" or r'구매|구입|\b산\b' in no_space_text else 0
                    query[f'{add_str}{finance_type}_simple'] = f"SELECT rp_date, rp_detail, rp_amount FROM tb_received_paid WHERE user_id = {{user_id}} AND rp_part = {rp_part} {add_query} {date_query}"



    elif finance_query == "예산":
        
        current_date = datetime.today()
        current_year = current_date.year
        this_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if re.fullmatch(r'\d{4}-\d{1,2}', input_time):
            input_date = datetime.strptime(input_time, "%Y-%m")

            if input_date < this_month:
                query["예외"] = f"과거 예산 조회는 불가능합니다.\n{this_month.strftime('%Y-%m')}만 조회가 가능합니다." 
            elif input_date > this_month or "추천" in text:
                query["다음달 예산추천"] = (
                    "SELECT AVG(rp_amount) AS monthly_average FROM tb_received_paid "
                    "WHERE user_id = {user_id} AND rp_date BETWEEN DATE_ADD(NOW(), INTERVAL -3 MONTH) AND NOW() AND rp_part = 1;"
                )
            else:
                query["예산"] = (
                    f'SELECT uf.uf_target_budget, rp.rp_amount FROM tb_user_finance uf CROSS JOIN tb_received_paid rp WHERE uf.user_id = {{user_id}} AND rp.user_id = {{user_id}} AND rp.rp_date LIKE ("{input_time}%")')
                

        elif re.fullmatch(r'\d{4}', input_time):
            input_year = int(input_time)

            if input_year < current_year:
                query["예외"] = f"과거 예산 조회는 불가능합니다.\n{this_month.strftime('%Y-%m')}만 조회가 가능합니다." 
            elif input_year > current_year or "추천" in text:
                query["올해 예산추천"] = (
                    'SELECT AVG(rp_amount) AS yearly_average FROM tb_received_paid '
                    'WHERE rp_date BETWEEN DATE_ADD(NOW(), INTERVAL -3 YEAR) AND NOW() AND rp_part = 1;'
                )
            else:
                query["예외"] = f"올해 예산 조회는 불가능합니다.\n{this_month.strftime('%Y-%m')}만 조회가 가능합니다." 



    elif finance_query == "저축":

        detail_conditions = {
            "예금": "rp_detail = '정기 예금'",
            "적금": "rp_detail = '적금'",
            "예적금": "(rp_detail = '정기 예금' OR rp_detail = '적금')",
            "저축": "(rp_detail = '정기 예금' OR rp_detail = '적금')",
            "저금": "(rp_detail = '정기 예금' OR rp_detail = '적금')",
        }
        for i in range(len(entity1)):
            detail_query = detail_conditions.get(entity1[i][0], "")

            if entity2[0][1] == "stats":
                query[f'{entity1[i][0]}_stats'] = f'SELECT rp_date, rp_detail, rp_amount, SUM(rp_amount) OVER () AS Total_Amount FROM tb_received_paid WHERE user_id = 10 AND rp_part = 1 AND {detail_query} {date_query} ORDER BY rp_date ASC'
                
            elif entity2[0][1] in ["sum", "date"]:
                sum_or_date = "SUM(rp_amount) AS Total_Amount" if entity2[0][1] == "sum" else "rp_date, rp_amount"
                query[f'{entity1[i][0]}_sum'] = f'SELECT rp_detail, {sum_or_date} FROM tb_received_paid WHERE user_id = {{user_id}} AND rp_part = 1 AND {detail_query} {date_query}'
            else:
                query[f'{entity1[i][0]}_simple'] = f'SELECT rp_date, rp_detail, rp_amount FROM tb_received_paid WHERE user_id = {{user_id}} AND rp_part = 1 AND {detail_query} {date_query} ORDER BY rp_date ASC'

        return query
    


    elif finance_query == "입출금":

        def is_deposit(text, e1):
            return any(word in text for word in ["입금", "들어온", "받은"]) or e1 == "입금"

        def is_withdrawal(text, e1):
            return any(word in text for word in ["출금", "납부", "인출", "나간", "보낸"]) or e1 in ["출금", "납부", "인출"]

        for i in range(len(entity1)):
            
            e1 = entity1[i][0]
            e2 = entity2[i][1] if len(entity2[i]) > 1 else None
            
            if e2 == "sum":
                if is_deposit(text, e1):
                    query[f"{add_str}입금_sum"] = f'SELECT SUM(rp_amount) as Total_amount FROM tb_received_paid WHERE user_id = {{user_id}} AND rp_detail = "입금" {add_query} {date_query}'
                elif is_withdrawal(text, e1):
                    query[f"{add_str}출금_sum"] = f'SELECT SUM(rp_amount) as Total_amount FROM tb_received_paid WHERE user_id = {{user_id}} AND rp_detail = "출금" {add_query} {date_query}'
            
            elif e2 == "sort":
                if any(word in text for word in ["큰", "크게", "높은"]):
                    sort_order = "DESC"
                    size_suffix = "_highest" if any(word in text for word in ["가장", "최고", "제일"]) else "_top5"
                elif any(word in text for word in ["작은", "적게", "낮은", "적은", "작게"]):
                    sort_order = "ASC"
                    size_suffix = "_lowest" if any(word in text for word in ["가장", "최고", "제일"]) else "_bottom5"
                else:
                    sort_order = None
                    size_suffix = ""

                # limit 설정
                limit = "1" if any(word in text for word in ["가장", "최고", "제일"]) else "5"
                
                # 자주 발생한 경우를 처리
                if any(word in text for word in ["자주", "많이", "빈번", "반복", "주요", "많은"]):
                    size_suffix = "_frequent"
                    # 입금/출금 여부에 따라 쿼리 생성
                    if is_deposit(text, e1):
                        query[f"{add_str}입금{size_suffix}"] = generate_query_TRANSACTION(
                            "입금", add_query=add_query, date_query=date_query, frequent=True
                        )
                    elif is_withdrawal(text, e1):
                        query[f"{add_str}출금{size_suffix}"] = generate_query_TRANSACTION(
                            "출금", add_query=add_query, date_query=date_query, frequent=True
                        )
                else:
                    # 입금/출금 여부에 따라 쿼리 생성 및 키 값 설정
                    if is_deposit(text, e1):
                        query[f"{add_str}입금{size_suffix}"] = generate_query_TRANSACTION(
                            "입금", add_query=add_query, date_query=date_query, order_by=sort_order, limit=limit
                        )
                    elif is_withdrawal(text, e1):
                        query[f"{add_str}출금{size_suffix}"] = generate_query_TRANSACTION(
                            "출금", add_query=add_query, date_query=date_query, order_by=sort_order, limit=limit
                        )
            elif e2 == "average":
                if is_deposit(text, e2):
                    query[f"{add_str}입금_avg"] = f'SELECT AVG(rp_amount) as Average_amount FROM tb_received_paid WHERE user_id = {{user_id}} AND rp_detail = "입금" {add_query} {date_query}'
                elif is_withdrawal(text, e2):
                    query[f"{add_str}출금_avg"] = f'SELECT AVG(rp_amount) as Average_amount FROM tb_received_paid WHERE user_id = {{user_id}} AND rp_detail = "출금" {add_query} {date_query}'

            else:
                if is_deposit(text, e1):
                    query[f"{add_str}입금_simple"] = f'SELECT rp_date, rp_detail, rp_amount FROM tb_received_paid WHERE user_id = {{user_id}} AND rp_detail = "입금" {add_query} {date_query}'
                elif is_withdrawal(text, e1):
                    query[f"{add_str}출금_simple"] = f'SELECT rp_date, rp_detail, rp_amount FROM tb_received_paid WHERE user_id = {{user_id}} AND rp_detail = "출금" {add_query} {date_query}'



    elif finance_query == "자산":
        query["링크"] = "https://localhost:3000/myassetplaner"



    elif finance_query == "대출":
        for _ in range(len(entity1)):
            if "상환" in text:
                # query['대출'] = 'SELECT uf_loan FROM tb_user_finance WHERE user_id = {user_id}'
                query['대출상환'] = f'SELECT uf.user_id, uf.uf_loan, rp.rp_date, rp.rp_detail, rp.rp_amount, ra.rp_all AS rp_all FROM tb_user_finance uf JOIN tb_received_paid rp ON uf.user_id = rp.user_id JOIN (SELECT sum(rp_amount) AS rp_all FROM tb_received_paid WHERE rp_detail="대출 상환"AND user_id={user_id}) AS ra ON uf.user_id = rp.user_id WHERE rp.rp_detail = "대출 상환" AND uf.user_id={user_id}' + " " + date_query
                # query['갚은대출'] = f'SELECT SUM(rp_amount) as sum_loan_amount FROM tb_received_paid WHERE user_id = {user_id} AND rp_detail = "대출 상환"'
                text = text.replace("상환", "", 1)
            elif "대출":
                query['대출'] = 'SELECT uf_loan FROM tb_user_finance WHERE user_id = {user_id}'
    


    elif finance_query == "가계부":
        query[f'전체내역'] = 'SELELT rp_date, rp_detail, rp_amount FROM tb_received_paid WHERE user_id = {user_id}' + " " + date_query
    return query



def pattern_stock(entity, input_date, text=None):  # [('삼성', 'STOCK'), ('애플', 'STOCK'), ('산', 'buy')]
    query, entity_list, entity_str = {}, [], ''
    buy = r"구매|구입|매입|매수|투자|사고|\b산\b"
    sell = r"판매|매도|\b판\b|처분|팔고"
    stock_mapping = {"삼성": "sh_ss_count", "삼전": "sh_ss_count", "samsung": "sh_ss_count",
                    "애플": "sh_ap_count", "apple": "sh_ap_count",
                    "비트코인": "sh_bit_count", "코인": "sh_bit_count", "bitcoin": "sh_bit_count", "coin": "sh_bit_count"}

    for i, j in entity:
        if i in stock_mapping:
            entity_list.append(stock_mapping[i])
            break
        for stock in entity_list:
            entity_str += f'{str(stock)}, '

    if sell in text and buy in text:
        date_query = process_date_format(input_date, date_query="AND sh_date IN (")
        if len(entity_list) == 0:
            query['주식거래'] = 'SELECT sh_date, sh_ss_count, sh_ap_count, sh_bit_count FROM tb_shares_held WHERE user_id = {{user_id}}' + date_query
        elif len(entity_list) == 1:
            query[f'{entity_list[0]}거래'] = f'SELECT {entity_str} FROM tb_shares_held' + ' WHERE user_id = {{user_id}}' + date_query
        else:
            for i in range(len(entity_list)):
                query[f'{entity_list[i]}거래'] = f'SELECT {entity_str} FROM tb_shares_held' + ' WHERE user_id = {{user_id}}' + date_query
        return query
    elif buy in text:
        date_query = process_date_format(input_date, date_query="AND sh_date IN (")
        if len(entity_list) == 0:
            query['주식구매'] = 'SELECT sh_date, sh_ss_count, sh_ap_count, sh_bit_count FROM tb_shares_held WHERE user_id = {{user_id}} AND (sh_ss_count > 0 OR sh_ap_count > 0 OR sh_bit_count > 0)' + " " + date_query
        elif len(entity_list) == 1:
            query[f'{entity_list[0]}구매'] = f'SELECT {entity_str} FROM tb_shares_held' + ' WHERE user_id = {{user_id}}' + f' AND {entity_list[0]} > 0' + " " + date_query
        else:
            for i in range(len(entity_list)):
                query[f'{entity_list[i]}구매'] = f'SELECT {entity_str} FROM tb_shares_held' + ' WHERE user_id = {{user_id}}' + f' AND {entity_list[i]} > 0' + " " + date_query
        return query
    elif sell in text:
        date_query = process_date_format(input_date, date_query="AND sh_date IN (")
        if len(entity_list) == 0:
            query['주식판매'] = 'SELECT sh_date, sh_ss_count, sh_ap_count, sh_bit_count FROM tb_shares_held WHERE user_id = {{user_id}} AND (sh_ss_count < 0 OR sh_ap_count < 0 OR sh_bit_count < 0)' + " " + date_query
        elif len(entity_list) == 1:
            query[f'{entity_list[0]}판매'] = f'SELECT {entity_list[0]} FROM tb_shares_held' + ' WHERE user_id = {{user_id}}' + f' AND {entity_list[0]} < 0' + " " + date_query
        else:
            for i in range(len(entity_list)):
                query[f'{entity_list[i]}판매'] = f'SELECT {entity_list[i]} FROM tb_shares_held' + ' WHERE user_id = {{user_id}}' + f' AND {entity_list[i]} < 0' + " " + date_query
        return query
    else:
        date_query = process_date_format_stock_qty(input_date, date_type="%Y-%m-%d")
        if len(entity_list) == 0:
            query['주식내역'] = 'SELECT sh_date, SUM(sh_ss_count) as total_ss, SUM(sh_ap_count) as total_ap, SUM(sh_bit_count) as total_bit FROM tb_shares_held WHERE user_id = {{user_id}}' + " " + date_query
        elif len(entity_list) == 1:
            query[f'{entity_list[0]}주식내역'] = f'SELECT SUM({entity_list[0]}) as total_{entity_list[0]} FROM tb_shares_held WHERE user_id = {{user_id}} {date_query}'
        else:
            for i in range(len(entity_list)):
                query[f'{entity_list[i]}주식내역'] = f'SELECT SUM({entity_list[i]}) as total_{entity_list[i]} FROM tb_shares_held WHERE user_id = {{user_id}} {date_query}'
        return query


# 앤티티 2개일때, 1개만 남기기
def filter_entities(entities):
    entity_map = {
        "자산": 0,             # 보유|자산|재정|재무|자본|재산|잔고
        "가계부": 0,               # 가계부 등
        "주식": 2,             # 주식|삼성|삼전|애플|코인|비트코
        "저축": 2,   # 적금|예금|저축
        "대출": 2,              # 대출
        "소득": 2,            # 소득|소득|월급|급여
        "예산": 2,            # 예산
        "입출금": 1,       # 입출금|입금|출금|이체|송금|인출|납부
        "지출": 1        # 지출|소비|쓴|사용|결제|카드
    }

    vs = []
    for i in entities:
        a = {i : entity_map[i]}
        vs.append(a)

    vs2 = {}
    for i in vs:
        if len(vs2) != 0:
            ivalue = list(i.values())
            vs2value = list(vs2.values())
            if ivalue[0] > vs2value[0]:
                vs2.clear()
                vs2[list(i.keys())[0]] = list(i.values())[0]
            elif ivalue[0] == vs2value[0]:
                vs2[list(i.keys())[0]] = list(i.values())[0]
        else:
            vs2[list(i.keys())[0]] = list(i.values())[0]
    return list(vs2.keys())


def process_fixed_dates_original(input_date, text):

    if isinstance(input_date, str):
        input_date = [input_date]
    input_dates = []

    # "고정"이 text에 포함된 경우 처리
    if input_date == None:
        date_query = ""

    elif "고정" in text or "고 정" in text:
        for x in range(len(input_date)):
            today_str = datetime.now(kst).strftime("%Y-%m-%d" if len(input_date[x]) == 10 else "%Y-%m" if len(input_date[x]) == 7 else "%Y")
            today = datetime.strptime(today_str, "%Y-%m-%d" if len(today_str) == 10 else "%Y-%m" if len(input_date[x]) == 7 else "%Y")
            input_date_compare = datetime.strptime(input_date[x], "%Y-%m-%d" if len(input_date[x]) == 10 else "%Y-%m" if len(input_date[x]) == 7 else "%Y")
            
            # input_date가 현재 날짜와 동일한 경우
            if input_date_compare == today or  input_date_compare > today:
                today = datetime.now(kst)
                one_year_ago  = today - relativedelta(years=1)
                one_month_ago = today - relativedelta(months=1)

                for day in input_date:
                    day_str = str(day)
                    if len(day_str) == 10:
                        input_dates.append(today.strftime("%Y-%m-%d"))

                    elif len(day_str) == 7:
                        start_date = one_month_ago + timedelta(days=1)
                        end_date = today
                        while start_date <= end_date:
                            input_dates.append(start_date.strftime("%Y-%m-%d"))
                            start_date += timedelta(days=1)

                    elif len(day_str) == 4:
                        start_date = one_year_ago + timedelta(days=1)
                        end_date = today
                        while start_date <= end_date:
                            input_dates.append(start_date.strftime("%Y-%m-%d"))
                            start_date += timedelta(days=1)

            # input_date가 현재 날짜보다 과거인 경우
            elif input_date_compare < today:
                input_dates.append(input_date[x])

    date_query = process_date_format(input_dates) if input_date else ""
    return date_query


# 쿼리 추출 함수
def finance_create_query(text):

    entity = extract_finance_entities(text)
    entity1 = (entity['pattern1'])
    entity2 = (entity['pattern2'])

    original_input_date  = split_and_return_periods(text, False)
    input_date = original_input_date

    entity1pattern = []
    for i in range(len(entity1)):
        entity1pattern.append(entity1[i][1])
    entity1pattern = list(set(entity1pattern))

    if "대출" in entity1pattern or "저축" in entity1pattern:
        if not input_date:
            input_date = None
    else:
        if not input_date:
            input_date = [datetime.now(kst).strftime("%Y-%m")]

    date_query_fixed = process_fixed_dates_original(input_date, text)

    if "주식" in entity1pattern or r"매입|매수|투자|판매|매매|매도|\b판\b|처분" in text:
        return pattern_stock(entity1, input_date, text=text)

    else:
        entity1pattern = filter_entities(entity1pattern)

        if len(entity1pattern) == 1:
            entity1pattern = entity1pattern[0]

        if entity1pattern == "지출" or entity1pattern == "소득" or r'구매|구입|\b산\b' in text:
            if "고정" in text or "고 정" in text:
                return finance_pattern_query(finance_query=entity1pattern, entity1=entity1, entity2=entity2, text=text, date_query=date_query_fixed)
            if not input_date:
                input_date = datetime.strftime(datetime.today(), '%Y-%m-%d')
                date_query = process_date_format(input_date)
            else:
                date_query = process_date_format(input_date)
            return finance_pattern_query(finance_query=entity1pattern, entity1=entity1, entity2=entity2, date_query=date_query, text=text)

        elif entity1pattern == "예산":
            input_date = split_and_return_periods(text, True)
            if input_date == None or len(input_date) == 7:
                input_date = [datetime.strftime(datetime.today(), '%Y-%m')]
            input_month = input_date[0]
            return finance_pattern_query(entity1pattern, input_month, text=text)

        elif entity1pattern == "대출":
            date_query = process_date_format(input_date, date_type='%Y-%m')
            return finance_pattern_query(finance_query=entity1pattern, entity1=entity1, entity2=entity2, text=text, date_query=date_query)

        elif entity1pattern == "저축":
            if "고정" in text or "고 정" in text:
                return finance_pattern_query(finance_query=entity1pattern, entity1=entity1, entity2=entity2, text=text, date_query=date_query_fixed)
            date_query = process_date_format(input_date, date_type="%Y-%m-%d")
            return finance_pattern_query(finance_query=entity1pattern, entity1=entity1, entity2=entity2, date_query=date_query, text=text)

        elif entity1pattern == "입출금":
            date_query = process_date_format(input_date, date_type='%Y-%m')
            if "고정" in text:
                return finance_pattern_query(finance_query=entity1pattern, entity1=entity1, entity2=entity2, text=text, date_query=date_query_fixed)
            else:
                return finance_pattern_query(finance_query=entity1pattern, entity1=entity1, entity2=entity2, text=text, date_query=date_query)
        elif entity1pattern == "자산":
            return finance_pattern_query(finance_query=entity1pattern, text=text)

        elif entity1pattern == "가계부":
            date_query = process_date_format(input_date, date_type='%Y-%m')
            return finance_pattern_query(finance_query=entity1pattern, entity1=entity1, date_query=date_query, text=text)

        elif len(entity1pattern) == 0:
            query = { "예외": "질문에서 사용자의 의도파악에 실패하였습니다." }
            return query
        else:
            query = { "예외": "죄송합니다. 2개 이상의 재무정보는 한번에 답변이 불가능합니다." }
            return query

def finance_clean_query(text):
    query = finance_create_query(text)
    complite_query = {}
    temp_value = set()
    for i, j in query.items():
        if j not in temp_value:
            complite_query[i] = j
            temp_value.add(j)
    return complite_query

def stockpricequery(text):
    entities = extract_stock_entities(text)
    stock_labels = ["삼성전자", "애플", "비트코인"]
    requested_stocks = [stock for stock in stock_labels if stock in entities]

    if not requested_stocks:
        return {"예외": "조회할 주식 종목을 명확히 알려주세요."}

    # 날짜 처리
    today = datetime.now(kst)
    yesterday = today - timedelta(days=1)
    dates = split_and_return_periods(text, True)  # 미래 날짜도 포함
    if dates:
        converted_dates = []
        for date_str in dates:
            try:
                if len(date_str) == 10:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                elif len(date_str) == 7:
                    date_obj = datetime.strptime(date_str, '%Y-%m')
                elif len(date_str) == 4:
                    date_obj = datetime.strptime(date_str, '%Y')
                else:
                    continue
                date_obj = kst.localize(date_obj)
                converted_dates.append(date_obj)
            except ValueError:
                continue
        past_dates = [date for date in converted_dates if date <= today]
        if not past_dates:
            return {"예외": "미래 예측 데이터는 이곳에서 확인해 주세요.\nhttps://localhost:3000/stockprediction"}
    else:
        # 날짜가 없으면 오늘 날짜로 설정
        past_dates = [yesterday]

    # 날짜 조건 생성
    date_conditions = []
    for date_obj in past_dates:
        date_str = date_obj.strftime('%Y-%m-%d')
        date_conditions.append(f"'{date_str}'")
    date_condition = f"fd_date IN ({', '.join(date_conditions)})"  # 컬럼 이름 수정

    # 종목별 컬럼 매핑
    stocks_map = {
        "삼성전자": "sc_ss_stock",
        "애플": "sc_ap_stock",
        "비트코인": "sc_coin"
    }

    # SQL 쿼리 생성
    stock_column = stocks_map.get(requested_stocks[0])
    if not stock_column:
        return {"예외": "해당 주식 종목에 대한 정보가 없습니다."}
    query = f"SELECT fd_date, {stock_column} FROM tb_stock WHERE {date_condition} ORDER BY fd_date DESC;"  # 컬럼 이름 수정
    return {f"{requested_stocks[0]}_주가": query}

def stock_information_query(text):
    entities = extract_stock_entities(text)
    stock_map = {
        "삼성전자": {
            "PBR": "sc_ss_pbr",
            "PER": "sc_ss_per",
            "ROE": "sc_ss_roe",
            "MC": "sc_ss_mc",
            "StockPrice": "sc_ss_stock"  # 주가 컬럼 추가
        },
        "애플": {
            "PBR": "sc_ap_pbr",
            "PER": "sc_ap_per",
            "ROE": "sc_ap_roe",
            "MC": "sc_ap_mc",
            "StockPrice": "sc_ap_stock"  # 주가 컬럼 추가
        },
        "비트코인": {
            "MC": "sc_coin",
            "StockPrice": "sc_coin"  # 주가 컬럼 추가
        }
    }
    stock_labels = stock_map.keys()
    info_labels = {"PBR", "PER", "ROE", "MC"}

    # 사용자 입력에서 주식 종목과 금융 지표 추출
    requested_stocks = [stock for stock in stock_labels if stock in entities]
    requested_infos = [info for info in info_labels if info in entities]

    if not requested_stocks:
        return {"예외": "조회할 주식 종목을 명확히 알려주세요."}
    if not requested_infos:
        return {"예외": "조회할 정보를 명확히 알려주세요. (PER, PBR, ROE, 시가총액 등)"}

    # 날짜 처리
    today = datetime.now(kst)
    yesterday = today - timedelta(days=1)
    dates = split_and_return_periods(text, True)  # 미래 날짜 포함
    if dates:
        converted_dates = []
        for date_str in dates:
            try:
                if len(date_str) == 10:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                elif len(date_str) == 7:
                    date_obj = datetime.strptime(date_str, '%Y-%m')
                elif len(date_str) == 4:
                    date_obj = datetime.strptime(date_str, '%Y')
                else:
                    continue
                date_obj = kst.localize(date_obj)
                converted_dates.append(date_obj)
            except ValueError:
                continue
        past_dates = [date for date in converted_dates if date <= today]
        if not past_dates:
            return {"예외": "미래 날짜의 정보는 제공할 수 없습니다."}
    else:
        # 날짜가 없을 경우 최신 날짜로 설정
        past_dates = [yesterday]

    # 날짜 조건 생성
    date_conditions = []
    for date_obj in past_dates:
        date_str = date_obj.strftime('%Y-%m-%d')
        date_conditions.append(f"'{date_str}'")
    date_condition = f"fd_date IN ({', '.join(date_conditions)})"

    # SQL 쿼리 생성
    queries = {}
    for stock in requested_stocks:
        for info in requested_infos:
            stock_info_column = stock_map.get(stock, {}).get(info)
            stock_price_column = stock_map.get(stock, {}).get('StockPrice')
            if not stock_info_column or not stock_price_column:
                continue  # 해당 정보가 없으면 건너뜀
            query_key = f"{stock}_{info}"
            query = f"SELECT fd_date, {stock_info_column}, {stock_price_column} FROM tb_stock WHERE {date_condition} ORDER BY fd_date DESC;"
            queries[query_key] = query

    if not queries:
        return {"예외": "해당 정보가 없습니다."}

    return queries

def predict_stock_query():
    return "주식/코인에 대한 예상값은 다음 링크를 참조하세요: {PS_LINK}"

def economic_indicator_query():
    return "경제지표에 대한 자세한 정보는 다음 링크를 참조하세요: {EI_LINK}"

def stock_create_quary(text):
    entities = extract_stock_entities(text)
    # if len(entities) >= 3:
    #     return {"예외": "하나의 질문만 해주세요."}

    if any(info in entities for info in ["PBR", "PER", "ROE", "MC"]):
        stock_info_query = stock_information_query(text)
        return stock_info_query
    elif "주가" in entities:
        stock_price_query = stockpricequery(text)
        return stock_price_query
    elif "예상" in entities:
        return predict_stock_query()
    elif "경제지표" in entities:
        return economic_indicator_query()
    elif "증시" in entities:
        
        return {"증시": f"{stock_market_news}"}
    else:
        return {"예외": "올바른 주식 관련 질문을 해주세요."}

def make_query(predict, text):
    if predict == 'finance':
        return finance_clean_query(text)
    elif predict == 'stock':
        return stock_create_quary(text)
    elif predict == 'FAQ':
        return { 'FAQ' : 'https://localhost:3000/faq' }




# ================================================================================ Economic Entity Function ================================================================================
def extract_finance_entities(text):
    patterns = {
        "지출": r"지출|소비|쓴|사용|결제|카드",
        "소득": r"수입|소득|월급|급여",
        "예산": r"예산",
        "대출": r"대출",
        "저축": r"적금|예금|저축|저금|예적금",
        "입출금": r"입출금|입금|출금|이체|송금|인출|납부|입금내역",
        "자산" : r"보유|자산|재정|재무|자본|재산|잔고",
        "주식" : r"주식|삼성|삼전|애플|코인|비트코인|samsung|apple|coin|bitcoin",
        "구매" : r"구매|구입|매입|매수|투자|\b산\b",
        "판매" : r"판매|매도|\b판\b|처분",
        "가계부": r"가계부|가계|금전",
    }
    patterns2 = {
        "stats" : r"비교|통계|보고|정리|분석|현황",  # 내역+합계
        "simple" : r"내역|상황|항목|목록|기록|출처|조회|정보|사항|이력|내용",  # 내역
        "sum" : r"합계|총액|총 금액|잔액|잔고|총합|누적|합산|총계|전체금액|최종금액",  # 합계
        "average" : r"평균",  # 평균
        "date" : r"언제",  # 날짜
        "sort" : r"가장|큰|크게|작은|제일|많이|적게|높은|높게|낮은|낮게|순위|순서|자주|반복|빈번|주요|적은|많은",  # 정렬
    }

    # 패턴에 맞는 주요 키워드 추출 함수
    def extract_main_keyword(text, pattern):
        match = re.search(pattern, text)
        if match:
            return match.group(0)
        return None

    # 텍스트에서 조사를 제거하는 함수
    def clean_text(text):
        cleaned_text = re.sub(r'(과|와|의|가|이|을|를|은|는|에서|으로|고|까지|부터|도|만|조차|뿐|에|와|에서|로)$', '', text)
        return cleaned_text

    # 사용자 정의 spaCy 파이프라인 컴포넌트
    @spacy.Language.component("custom_finance_entity_adder")
    def custom_finance_entity_adder(doc):
        ents = []
        seen_tokens = set()

        for token in doc:
            text_cleaned = clean_text(token.text)
            # patterns1 검사
            for label, pattern in patterns.items():
                main_keyword = extract_main_keyword(text_cleaned, pattern)
                if main_keyword and token.i not in seen_tokens:
                    ent = Span(doc, token.i, token.i + 1, label=f"{label}_pattern1")
                    ent._.set("cleaned_text", text_cleaned)
                    ents.append(ent)
                    seen_tokens.add(token.i)
                    break

            for label, pattern in patterns2.items():
                main_keyword = extract_main_keyword(text_cleaned, pattern)
                if main_keyword and token.i not in seen_tokens:
                    ent = Span(doc, token.i, token.i + 1, label=f"{label}_pattern2")
                    ent._.set("cleaned_text", text_cleaned)
                    ents.append(ent)
                    seen_tokens.add(token.i)
                    
        doc.ents = ents
        return doc
    
    # spaCy 모델 로드
    nlp = spacy.load("ko_core_news_sm")
    Span.set_extension("cleaned_text", default=None, force=True)

    # custom_finance_entity_adder가 이미 파이프라인에 존재하면 제거
    if "custom_finance_entity_adder" in nlp.pipe_names:
        nlp.remove_pipe("custom_finance_entity_adder")
    nlp.add_pipe("custom_finance_entity_adder", after="ner")
    doc = nlp(text)
    
    # 엔티티 결과 수집
    entities = {f"pattern{i}": [(ent._.get("cleaned_text"), ent.label_.replace(f"_pattern{i}", "")) for ent in doc.ents if f"_pattern{i}" in ent.label_] for i in (1, 2)}
    if not entities['pattern2']:
        entities['pattern2'].append(('기본값', 'simple'))

    return entities

def extract_stock_entities(text):
    """주어진 텍스트에서 주식 관련 엔티티를 추출하는 통합 함수입니다."""
    
    # 주식 관련 패턴 정의
    patterns1 = {
        "주가": r"주가|주식|종가|가격|값",
        "증시": r"증시|뉴스",
        "예상": r"예상|예측|전망|앞으로",
        "삼성전자": r"삼성전자|삼성|삼전|samsung",
        "애플": r"애플|apple",
        "비트코인": r"비트코인|bitcoin|비트|코인|coin",
        "PER": r"PER|per|주가수익비율|Price Earning Ratio",
        "PBR": r"PBR|pbr|주가순자산비율|Price Book-value Ratio",
        "ROE": r"ROE|roe|자기자본이익률|Return on Equity",
        "MC": r"MC|mc|시가총액|총액|시총|Market Cap",
        "경제지표":r"경제지표|국내총생산|GDP|기준금리|IR|수입물가지수|IPI|생산자물가지수|PPI|소비자물가지수|CPI|외환보유액"
    }

    # 패턴 통합
    combined_patterns = {**patterns1}

    # 텍스트에서 패턴에 맞는 주요 키워드 추출
    def extract_main_keyword(text, pattern):
        match = re.search(pattern, text)
        if match:
            return match.group(0)  # 매칭된 주요 키워드 반환
        return None  # 매칭되지 않으면 None 반환

    def clean_text(text):
        # Komoran으로 형태소 분석을 수행
        token_pos = komoran.pos(text)
        cleaned_tokens = [word for word, pos in token_pos if not pos.startswith('J')]
        cleaned_text = ''.join(cleaned_tokens)

        return cleaned_text

    # 사용자 정의 spaCy 파이프라인 컴포넌트
    @spacy.Language.component("custom_stock_entity_adder")
    def custom_stock_entity_adder(doc):
        new_ents = []

        for token in doc:
            # 형태소 분석을 통해 명사와 동사/형용사 추출
            token_pos = komoran.pos(token.text)
            
            # 품사별로 나눠서 명사 및 동사 추출
            noun_phrase = ''.join([word for word, tag in token_pos if tag in ['NNG', 'NNP', 'SL']])  # 명사
            verb_phrase = ''.join([word for word, tag in token_pos if tag in ['VV', 'VA']])  # 동사/형용사

            # 형태소 분석 결과와 원래 텍스트 보정
            noun_phrase_cleaned = clean_text(noun_phrase)  # 형태소 분석된 명사에서 조사를 제거
            original_text_cleaned = clean_text(token.text)  # 원래 텍스트에서 조사를 제거

            found = False  # 해당 단어가 패턴과 매칭되는지 확인
            for label, pattern in combined_patterns.items():
                if noun_phrase_cleaned and len(noun_phrase_cleaned) > 1:  # 명사가 있으면
                    main_keyword = extract_main_keyword(noun_phrase_cleaned, pattern)
                    if main_keyword:
                        found = True
                        new_ent = Span(doc, token.i, token.i + 1, label=label)
                        new_ent._.set("cleaned_text", noun_phrase_cleaned)
                        new_ents.append(new_ent)
                        break

                if verb_phrase:  # 동사/형용사가 있으면
                    main_keyword = extract_main_keyword(verb_phrase, pattern)
                    if main_keyword:
                        found = True
                        new_ent = Span(doc, token.i, token.i + 1, label=label)
                        new_ent._.set("cleaned_text", verb_phrase)
                        new_ents.append(new_ent)
                        break

            if not found:
                # 원래 텍스트에 기반해 패턴 매칭 시도
                main_keyword = extract_main_keyword(original_text_cleaned, pattern)
                if main_keyword:
                    new_ent = Span(doc, token.i, token.i + 1, label=label)
                    new_ent._.set("cleaned_text", original_text_cleaned)
                    new_ents.append(new_ent)
                    break

        # 최종 엔티티 설정
        doc.ents = new_ents

        return doc

    # spaCy 모델 로드
    nlp = spacy.load("ko_core_news_sm")

    # 확장 속성 등록
    Span.set_extension("cleaned_text", default=None, force=True)

    # 기존 파이프라인에서 custom_stock_entity_adder 제거
    if "custom_stock_entity_adder" in nlp.pipe_names:
        nlp.remove_pipe("custom_stock_entity_adder")

    # custom_stock_entity_adder 추가
    nlp.add_pipe("custom_stock_entity_adder", after="ner")

    # 텍스트 처리
    doc = nlp(text)

    # 결과 출력
    entities = [ent._.get("cleaned_text") for ent in doc.ents] + [ent.label_ for ent in doc.ents]
    return list(set(entities))


# ================================================================================ Model Load ================================================================================
# current_dir = os.path.dirname(os.path.abspath(__file__))
current_dir = r"C:\Users\dlavk\SEBIN\AICC_TEAM\aicc_contest\aicc_map\server\src\Algorithm\script"
tokenizer = AutoTokenizer.from_pretrained(current_dir)
model = AutoModelForSequenceClassification.from_pretrained(current_dir, num_labels=3)




# ================================================================================ Return Query Function ================================================================================
# 텍스트 전처리
spacing = Spacing()

def processe_text(text):
    text = spacing(text)
    text = re.sub(r"[^가-힣a-zA-Z0-9\s]", "", text)
    text = repeat_normalize(text, num_repeats=3)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def predict_label(text, model, tokenizer):
    # 토큰화
    inputs = tokenizer(text, return_tensors="pt", padding="max_length", truncation=True, max_length=512)
    # 모델 예측
    outputs = model(**inputs)
    probs = torch.softmax(outputs.logits, dim=-1)
    pred = torch.argmax(probs, dim=1).item()

    label_map = {0: 'stock', 1: 'finance', 2: 'FAQ'}
    return label_map[pred]

def format_number_korean(num):
    units = [("조", 1e12), ("억", 1e8), ("만", 1e4), ("", 1)]
    for unit_name, unit_value in units:
        if num >= unit_value:
            value = num / unit_value
            if unit_name:
                return f"{value:.2f}{unit_name}"
            else:
                return f"{int(value)}"
    return str(num)


# ================================================================================ Sentence Creation Function ================================================================================

def month_plus(data, text_message):
        
    this_month = int(datetime.strftime(datetime.today(), '%m'))
    next_month =  this_month + 1
    next_month = 1 if next_month == 13 else next_month
    step = 0

    if any(phrase in text_message for phrase in ["다음달", "다음 달", f"{next_month}월"]):
        step = 2
    elif any(phrase in text_message for phrase in ["이번달", "이번 달", f"{this_month}월"]):
        step = 1

    if step > 0:
        for i in range(len(data)):
            data[i]['rp_date'] = datetime.strptime(data[i]['rp_date'], '%Y-%m-%d')
            data[i]['rp_date'] = data[i]['rp_date'] + relativedelta(months=step)
            data[i]['rp_date'] = data[i]['rp_date'].strftime('%Y-%m-%d')           
    
    return data

def format_date(date_str):
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime("%Y년 %m월 %d일")
        except ValueError:
            continue
    return None


# 지출/소득/입출금/예적금
def make_answer(data, front_key, backword_key, text_message):

    if "고정" in text_message or "고 정" in text_message:
        data = month_plus(data, text_message)  

    if backword_key == 'simple':
        final_sentence = f"{front_key}내역:\n"
        for part in data:
            date_data = part['rp_date']
            detail_data = part['rp_detail']
            amount_data = f"{part['rp_amount']:,}"
            sentence = f'{date_data} :  {detail_data}\t| {amount_data}원\n'
            final_sentence += sentence
        return final_sentence
    
    elif backword_key == 'sum':
        data[0]['Total_amount'] = int(data[0]['Total_amount'])
        sentence = f"{front_key} 총 금액은 {data[0]['Total_amount']:,}원 입니다."
        return sentence
    
    elif backword_key == 'avg':
        data[0]['Average_amount'] = int(float(data[0]['Average_amount']))
        sentence = f"{front_key} 평균 금액은 {data[0]['Average_amount']:,}원 입니다."
        return sentence
    
    elif backword_key == 'highest':
        date_data = data[0]['rp_date']
        detail_data = data[0]['rp_detail']
        amount_data = f"{data[0]['rp_amount']:,}"
        sentence = f"가장 높았던 {front_key}은 {date_data}에 {detail_data}으로 {amount_data}원 입니다."
        return sentence
    
    elif backword_key == 'top5':
        sentence = f"{front_key} 금액 높은 순위 TOP5:\n"
        for part in data:
            date_data = part['rp_date']
            detail_data = part['rp_detail']
            amount_data = f"{part['rp_amount']:,}"
            sentence += f'{date_data} :  {detail_data}\t| {amount_data} 원\n'
        if len(data) < 5:
            sentence = sentence + "\n 추가 해당하는 내역이 없습니다."
        return sentence
    
    elif backword_key == 'lowest':
        date_data = data[0]['rp_date']
        detail_data = data[0]['rp_detail']
        amount_data = f"{data[0]['rp_amount']:,}"
        sentence = f"가장 낮았던 {front_key}은 {date_data}에 {detail_data}으로 {amount_data}원 입니다."
        return sentence
    
    elif backword_key == 'bottom5':
        sentence = f"{front_key} 금액 낮은 순위 TOP5:\n"
        for part in data:
            date_data = part['rp_date']
            detail_data = part['rp_detail']
            amount_data = f"{part['rp_amount']:,}"
            sentence += f'{date_data} :  {detail_data}\t| {amount_data} 원\n'
        if len(data) < 5:
            sentence = sentence + "\n 추가 해당하는 내역이 없습니다."
        return sentence
    
    elif backword_key == 'frequent':
        sentence = f"자주 있는 {front_key} 내역:\n"
        for part in data:
            date_data = part['rp_date']
            detail_data = part['rp_detail']
            amount_data = f"{part['rp_amount']:,}"
            sentence += f'{date_data} :  {detail_data}\t| {amount_data} 원\n'
        return sentence
    
    elif backword_key == 'stats':
        amount = int(data[0]['Total_Amount'])
        final_sentence = f"{front_key} 내역:\n"
        for part in data:
            date_data = part['rp_date']
            detail_data = part['rp_detail']
            amount_data = f"{part['rp_amount']:,}"
            sentence = f'{date_data} :  {detail_data}\t| {amount_data} 원\n'
            final_sentence += sentence
        final_sentence = f'{final_sentence}\n{front_key}한 총 금액은 {amount:,}원 입니다.'
        return final_sentence
    

# 예산
def budget_answer(query, front_key):
    if front_key == "예산":
        budget = query[0]["uf_target_budget"]
        paied_amount = query[0]["rp_amount"]
        month = datetime.now().strftime("%Y년 %m월")
        result = f"{month} 예산은 {budget:,}원 입니다.\n 사용 금액을 제외한 남은 예산금액은 {(budget-paied_amount):,}원 입니다."
        return result
    
    elif front_key == "올해 예산":
        return query

    elif front_key == "다음달 예산추천":
        result = f"다음달 예산으로 {int(float(query[0]['monthly_average'])):,}원을 추천 드립니다.\n 예산 추천은 최근 3개월 소비를 분석하여 답변해드립니다."
        return result
    
    elif front_key == "올해 예산추천":
        result = f"올해 예산으로 {int(float(query[0]['yearly_average'])):,}원을 추천 드립니다.\n 예산 추천은 최근 3개년 소비를 분석하여 답변해드립니다."
        return result

    elif front_key == "과거 예산 조회":
        return query

# 대출
def loan_answer(query, front_key):
    
    if (front_key =="대출상환") or (front_key =="대출 상환"):
        loan = query[0]["uf_loan"]   
        final_sentence = f"{front_key}내역:\n"
        for part in query:
            date_data = part['rp_date']
            detail_data = part['rp_detail']
            amount_data = f"{part.get('rp_amount', 0):,}"
            sentence = f'{date_data} :  {detail_data}\t| {amount_data}원\n'
            final_sentence += sentence
            paid_loan = int(part['rp_all'])

        loan_balance = loan - paid_loan
        final_sentence = f'{final_sentence}\n 남은 대출금액: {loan_balance:,}원'
        return final_sentence
        
    elif front_key == "대출":
        loan = query[0].get('uf_loan', 0) if query else 0  # 리스트의 첫 번째 항목에서 대출 금액 가져옴   
        result = f"대출 총액은 {loan:,}원입니다."
        return result


def generate_stock_price_response(query_result, stock_name):
    if not query_result:
        return f"{stock_name}의 주가 정보를 찾을 수 없습니다."

    # 종목별 통화 단위 매핑
    currency_map = {
        '삼성전자': '원',
        '애플': '달러',
        '비트코인': '달러'
    }

    currency = currency_map.get(stock_name, '원')  # 기본값은 '원'으로 설정

    response = f"{stock_name}의 주가는:\n"
    if isinstance(query_result, list):
        for record in query_result:
            date = record.get('fd_date', '').split('T')[0]
            price = record.get('sc_ss_stock') or record.get('sc_ap_stock') or record.get('sc_coin')
            if price is not None:
                response += f"{date[:4]}년{date[5:7]}월{date[8:10]}일의 전일 종가 기준 {price}{currency} 입니다."
    elif isinstance(query_result, dict):
        record = query_result
        date = record.get('fd_date', '').split('T')[0]
        price = record.get('sc_ss_stock') or record.get('sc_ap_stock') or record.get('sc_coin')
        if price is not None:
            response += f"{date[:4]}년{date[5:7]}월{date[8:10]}일 전일 종가 기준 {price}{currency} 입니다."
    else:
        response += "데이터를 처리할 수 없습니다."

    return response


def generate_stock_info_response(query_result, keyword):
    if not query_result:
        return "해당 정보를 찾을 수 없습니다."

    response = ""
    # 종목명을 추출
    stock_name = keyword.split('_')[0]  # 예: '삼성전자_PER'에서 '삼성전자' 추출

    # 통화 단위 매핑
    currency_map = {
        '삼성전자': '원',
        '애플': '달러',
        '비트코인': '달러'  # 비트코인의 경우 필요에 따라 수정
    }
    currency = currency_map.get(stock_name, '원')  # 기본값은 '원'

    if isinstance(query_result, list):
        records = query_result
    elif isinstance(query_result, dict):
        records = [query_result]
    else:
        response += "데이터를 처리할 수 없습니다."
        return response.strip()

    for record in records:
        date = record.get('fd_date', '').split('T')[0]
        metric_value = None
        metric_name = ""
        stock_price = None

        if 'PER' in keyword:
            metric_value = record.get('sc_ss_per') or record.get('sc_ap_per')
            metric_name = f"{stock_name} PER"
        elif 'PBR' in keyword:
            metric_value = record.get('sc_ss_pbr') or record.get('sc_ap_pbr')
            metric_name = f"{stock_name} PBR"
        elif 'ROE' in keyword:
            metric_value = record.get('sc_ss_roe') or record.get('sc_ap_roe')
            metric_name = f"{stock_name} ROE"
        elif 'MC' in keyword:
            metric_value = record.get('sc_ss_mc') or record.get('sc_ap_mc')
            metric_name = f"{stock_name} 시가총액"
            # 시가총액 포맷팅
            if metric_value is not None:
                metric_value = float(metric_value)
                if stock_name == '삼성전자':
                    metric_value_formatted = format_number_korean(metric_value) + f" {currency}"
                elif stock_name == '애플':
                    if metric_value >= 1e12:
                        metric_value_formatted = f"{metric_value / 1e12:.2f}조 {currency}"
                    else:
                        metric_value_formatted = f"{metric_value / 1e8:.2f}억 {currency}"
                else:
                    metric_value_formatted = f"{metric_value:,} {currency}"
                metric_value = metric_value_formatted

        # 주가 정보 가져오기
        stock_price = record.get('sc_ss_stock') or record.get('sc_ap_stock') or record.get('sc_coin')
        if stock_price is not None:
            stock_price = float(stock_price)
            stock_price = f"{stock_price:,}{currency}"

        # 응답 문자열 구성
        if metric_value is not None and stock_price is not None:
            response += f"{date[:4]}년 {date[5:7]}월 {date[8:10]}일의 {metric_name}: {metric_value}"
        elif metric_value is not None:
            response += f"{date[:4]}년 {date[5:7]}월 {date[8:10]}일의 {metric_name}: {metric_value}"
        elif stock_price is not None:
            response += f"{date[:4]}년 {date[5:7]}월 {date[8:10]}일의 {stock_name}"

    return response.strip() if response else "해당 정보를 찾을 수 없습니다."


# ================================================================================ Chatbot req, res Data ================================================================================
# sys.stdin과 sys.stdout을 UTF-8로 설정
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

if __name__ == "__main__":
    while True:
        input_data = sys.stdin.readline().strip()
        if not input_data:
            continue  # 입력이 없으면 다시 대기 상태로 돌아감

        try:
            # 입력된 데이터를 JSON으로 파싱
            data = json.loads(input_data)

            # 전달된 데이터에서 message, user_id, query_result, key 추출
            message = data.get('message')
            user_id = data.get('user_id')
            query_result = data.get('queryResult')  # queryResult가 맞는지 확인
            keyword = data.get('key')
        

            # 첫 번째 입력 처리: message와 user_id가 있는 경우
            if message and user_id and not query_result and not keyword:
                message = processe_text(message)
                classification = predict_label(message, model, tokenizer)
                query = make_query(classification, message)

                for key in query:
                    query[key] = query[key].format(user_id=user_id)

                text_message = message[:]

                message = ''
                user_id = ''
                print(json.dumps(query, ensure_ascii=False) + '<END>', flush=True)

            # 두 번째 입력 처리: key와 query_result가 있는 경우
            elif keyword and query_result:
                for entry in query_result:
                    if 'rp_date' in entry:
                        query_time = datetime.strptime(entry['rp_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
                        korea_time = query_time.replace(tzinfo=pytz.utc).astimezone(kst)
                        entry['rp_date'] = korea_time.strftime("%Y-%m-%d")
                    elif 'fd_date' in entry:
                        query_time = datetime.strptime(entry['fd_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
                        korea_time = query_time.replace(tzinfo=pytz.utc).astimezone(kst)
                        entry['fd_date'] = korea_time.strftime("%Y-%m-%d")

                # 전달받은 queryResult 데이터로 처리
                try:
                    if "_" in keyword:
                        front_key = keyword.split("_")[0]
                        backword_key = keyword.split("_")[1]
                    else:
                        front_key = keyword

                    if (keyword == '예외') and ('https' in query_result) :
                        print(f'{query_result}', flush=True)
                    elif (keyword == '예외') and ('https' not in query_result) :
                        print(f'"{query_result}"\n올바른 형식으로 다시 질문해 주세요.', flush=True)
                    elif any(i in keyword for i in ['지출', '소득', '입금', '출금', '저축', '저금', '예적금', '예금', '적금']):
                        sentence = make_answer(query_result, front_key, backword_key, text_message)
                        print(sentence, flush=True)
                    elif '예산' in keyword: #in ['예산', '올해 예산', '올해 예산추천', '이번달 예산추천', "과거 예산 조회"]:
                        sentence = budget_answer(query_result, front_key)
                        print(sentence, flush=True)
                    elif '대출' in keyword:
                        sentence = loan_answer(query_result, front_key)
                        print(sentence, flush=True)
                    elif '링크' in keyword or 'FAQ' in keyword:
                        print(query_result, flush=True)
                    elif '주가' in keyword:
                        stock_name = keyword.replace('_주가', '')
                        sentence = generate_stock_price_response(query_result, stock_name)
                        print(sentence, flush=True)
                    elif any(metric in keyword for metric in ["PER", "PBR", "ROE", "MC"]):
                        response = generate_stock_info_response(query_result, keyword)
                        print(response, flush=True)
                    else:
                        print(json.dumps(query_result), flush=True)
                    query_result = ''
                    keyword = ''
                    text_message = ''
                except json.JSONDecodeError as e:
                    print(f"JSONDecodeError: {e}", flush=True)

            # key 또느 query_result의 값이 1개만 있을 때,
            elif (keyword and not query_result) or (not keyword and query_result):
                print("해당하는 결과를 찾을 수 없습니다. 다시 질문해 주세요.", flush=True)

        except json.JSONDecodeError:
            print("Error: 입력 데이터를 JSON으로 파싱하는 중 오류가 발생했습니다.", flush=True)
        except Exception as e:
            print(f"Error: {str(e)}", flush=True)
