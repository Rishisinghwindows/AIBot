"""
Pre-defined Conversation Flows

Contains flow definitions for common astrology operations.
"""

from common.flows.base import (
    FlowDefinition,
    FlowStep,
    StepType,
    validate_choice,
)


# =============================================================================
# BIRTH DETAILS FLOW
# =============================================================================

BIRTH_DETAILS_FLOW = FlowDefinition(
    name="birth_details",
    description="Collect birth date, time, and place",
    timeout_minutes=10,
    steps=[
        FlowStep(
            name="birth_date",
            prompt={
                "en": "What is your date of birth?",
                "hi": "आपकी जन्म तिथि क्या है?",
                "bn": "আপনার জন্ম তারিখ কি?",
                "ta": "உங்கள் பிறந்த தேதி என்ன?",
                "te": "మీ పుట్టిన తేదీ ఏమిటి?",
                "mr": "तुमची जन्मतारीख काय आहे?",
                "gu": "તમારી જન્મ તારીખ શું છે?",
            },
            prompt_key="flow.birth_details.date",
            step_type=StepType.DATE,
            field_name="birth_date",
            examples=["15-08-1990", "01-01-1985", "25-12-2000"],
            retry_prompt="Please enter date as DD-MM-YYYY (e.g., 15-08-1990)",
        ),
        FlowStep(
            name="birth_time",
            prompt={
                "en": "What was your time of birth?",
                "hi": "आपका जन्म समय क्या था?",
                "bn": "আপনার জন্ম সময় কি ছিল?",
                "ta": "உங்கள் பிறந்த நேரம் என்ன?",
                "te": "మీ పుట్టిన సమయం ఏమిటి?",
                "mr": "तुमचा जन्म वेळ काय होता?",
                "gu": "તમારો જન્મ સમય શું હતો?",
            },
            prompt_key="flow.birth_details.time",
            step_type=StepType.TIME,
            field_name="birth_time",
            examples=["10:30 AM", "6:00 PM", "14:30"],
            retry_prompt="Please enter time like 10:30 AM or 14:30",
        ),
        FlowStep(
            name="birth_place",
            prompt={
                "en": "Where were you born? (City/Town)",
                "hi": "आप कहाँ पैदा हुए थे? (शहर/गाँव)",
                "bn": "আপনি কোথায় জন্মগ্রহণ করেছেন? (শহর/গ্রাম)",
                "ta": "நீங்கள் எங்கே பிறந்தீர்கள்? (நகரம்/ஊர்)",
                "te": "మీరు ఎక్కడ పుట్టారు? (నగరం/పట్టణం)",
                "mr": "तुम्ही कुठे जन्मलात? (शहर/गाव)",
                "gu": "તમે ક્યાં જન્મ્યા હતા? (શહેર/ગામ)",
            },
            prompt_key="flow.birth_details.place",
            step_type=StepType.PLACE,
            field_name="birth_place",
            examples=["Delhi", "Mumbai", "Chennai"],
            retry_prompt="Please enter your birth city or town name",
        ),
    ],
    on_complete="birth_details_collected"
)


# =============================================================================
# LIFE PREDICTION FLOW
# =============================================================================

LIFE_PREDICTION_FLOW = FlowDefinition(
    name="life_prediction",
    description="Life prediction with birth details collection",
    timeout_minutes=10,
    steps=[
        FlowStep(
            name="prediction_type",
            prompt={
                "en": "What would you like to know about?",
                "hi": "आप किस बारे में जानना चाहते हैं?",
                "bn": "আপনি কি সম্পর্কে জানতে চান?",
                "ta": "நீங்கள் எதைப் பற்றி தெரிந்துகொள்ள விரும்புகிறீர்கள்?",
                "te": "మీరు దేని గురించి తెలుసుకోవాలనుకుంటున్నారు?",
                "mr": "तुम्हाला कशाबद्दल जाणून घ्यायचे आहे?",
                "gu": "તમે શું જાણવા માગો છો?",
            },
            prompt_key="flow.life_prediction.type",
            step_type=StepType.CHOICE,
            field_name="prediction_type",
            options=["Marriage", "Career", "Health", "Wealth", "Children", "Foreign Travel"],
        ),
        FlowStep(
            name="birth_date",
            prompt={
                "en": "What is your date of birth?",
                "hi": "आपकी जन्म तिथि क्या है?",
            },
            prompt_key="flow.birth_details.date",
            step_type=StepType.DATE,
            field_name="birth_date",
            examples=["15-08-1990", "01-01-1985"],
            retry_prompt="Please enter date as DD-MM-YYYY",
        ),
        FlowStep(
            name="birth_time",
            prompt={
                "en": "What was your time of birth?",
                "hi": "आपका जन्म समय क्या था?",
            },
            prompt_key="flow.birth_details.time",
            step_type=StepType.TIME,
            field_name="birth_time",
            examples=["10:30 AM", "6:00 PM"],
        ),
        FlowStep(
            name="birth_place",
            prompt={
                "en": "Where were you born?",
                "hi": "आप कहाँ पैदा हुए थे?",
            },
            prompt_key="flow.birth_details.place",
            step_type=StepType.PLACE,
            field_name="birth_place",
            examples=["Delhi", "Mumbai"],
        ),
    ],
    on_complete="life_prediction"
)


# =============================================================================
# KUNDLI MATCHING FLOW
# =============================================================================

KUNDLI_MATCHING_FLOW = FlowDefinition(
    name="kundli_matching",
    description="Collect birth details for two people for compatibility",
    timeout_minutes=15,
    steps=[
        # Person 1
        FlowStep(
            name="person1_name",
            prompt={
                "en": "Please provide details of the first person.\n\nWhat is the first person's name?",
                "hi": "कृपया पहले व्यक्ति का विवरण दें।\n\nपहले व्यक्ति का नाम क्या है?",
            },
            prompt_key="flow.kundli.person1.name",
            step_type=StepType.NAME,
            field_name="person1_name",
        ),
        FlowStep(
            name="person1_birth_date",
            prompt={
                "en": "First person's date of birth?",
                "hi": "पहले व्यक्ति की जन्म तिथि?",
            },
            step_type=StepType.DATE,
            field_name="person1_birth_date",
            examples=["15-08-1990"],
        ),
        FlowStep(
            name="person1_birth_time",
            prompt={
                "en": "First person's time of birth?",
                "hi": "पहले व्यक्ति का जन्म समय?",
            },
            step_type=StepType.TIME,
            field_name="person1_birth_time",
            examples=["10:30 AM"],
        ),
        FlowStep(
            name="person1_birth_place",
            prompt={
                "en": "First person's birth place?",
                "hi": "पहले व्यक्ति का जन्म स्थान?",
            },
            step_type=StepType.PLACE,
            field_name="person1_birth_place",
            examples=["Delhi"],
        ),
        # Person 2
        FlowStep(
            name="person2_name",
            prompt={
                "en": "Now the second person.\n\nWhat is the second person's name?",
                "hi": "अब दूसरे व्यक्ति के बारे में बताइए।\n\nदूसरे व्यक्ति का नाम क्या है?",
            },
            prompt_key="flow.kundli.person2.name",
            step_type=StepType.NAME,
            field_name="person2_name",
        ),
        FlowStep(
            name="person2_birth_date",
            prompt={
                "en": "Second person's date of birth?",
                "hi": "दूसरे व्यक्ति की जन्म तिथि?",
            },
            step_type=StepType.DATE,
            field_name="person2_birth_date",
            examples=["20-05-1992"],
        ),
        FlowStep(
            name="person2_birth_time",
            prompt={
                "en": "Second person's time of birth?",
                "hi": "दूसरे व्यक्ति का जन्म समय?",
            },
            step_type=StepType.TIME,
            field_name="person2_birth_time",
            examples=["2:30 PM"],
        ),
        FlowStep(
            name="person2_birth_place",
            prompt={
                "en": "Second person's birth place?",
                "hi": "दूसरे व्यक्ति का जन्म स्थान?",
            },
            step_type=StepType.PLACE,
            field_name="person2_birth_place",
            examples=["Mumbai"],
        ),
    ],
    on_complete="kundli_matching"
)


# =============================================================================
# DOSHA CHECK FLOW
# =============================================================================

DOSHA_CHECK_FLOW = FlowDefinition(
    name="dosha_check",
    description="Check for doshas with birth details",
    timeout_minutes=10,
    steps=[
        FlowStep(
            name="dosha_type",
            prompt={
                "en": "Which dosha would you like to check?",
                "hi": "आप कौन सा दोष जांचना चाहते हैं?",
            },
            step_type=StepType.CHOICE,
            field_name="dosha_type",
            options=["Manglik Dosha", "Kaal Sarp Dosha", "Sade Sati", "Pitra Dosha", "All Doshas"],
        ),
        FlowStep(
            name="birth_date",
            prompt={
                "en": "What is your date of birth?",
                "hi": "आपकी जन्म तिथि क्या है?",
            },
            step_type=StepType.DATE,
            field_name="birth_date",
            examples=["15-08-1990"],
        ),
        FlowStep(
            name="birth_time",
            prompt={
                "en": "What was your time of birth?",
                "hi": "आपका जन्म समय क्या था?",
            },
            step_type=StepType.TIME,
            field_name="birth_time",
            examples=["10:30 AM"],
        ),
        FlowStep(
            name="birth_place",
            prompt={
                "en": "Where were you born?",
                "hi": "आप कहाँ पैदा हुए थे?",
            },
            step_type=StepType.PLACE,
            field_name="birth_place",
            examples=["Delhi"],
        ),
    ],
    on_complete="dosha_check"
)


# =============================================================================
# HOROSCOPE FLOW (simple - just need zodiac sign)
# =============================================================================

HOROSCOPE_FLOW = FlowDefinition(
    name="horoscope",
    description="Get daily horoscope by zodiac sign",
    timeout_minutes=5,
    steps=[
        FlowStep(
            name="zodiac_sign",
            prompt={
                "en": "Which zodiac sign would you like the horoscope for?",
                "hi": "आप किस राशि का राशिफल चाहते हैं?",
            },
            step_type=StepType.CHOICE,
            field_name="zodiac_sign",
            options=[
                "Aries", "Taurus", "Gemini", "Cancer",
                "Leo", "Virgo", "Libra", "Scorpio",
                "Sagittarius", "Capricorn", "Aquarius", "Pisces"
            ],
        ),
        FlowStep(
            name="period",
            prompt={
                "en": "For which period?",
                "hi": "किस अवधि के लिए?",
            },
            step_type=StepType.CHOICE,
            field_name="period",
            options=["Today", "This Week", "This Month"],
        ),
    ],
    on_complete="get_horoscope"
)


# =============================================================================
# REGISTER FLOWS
# =============================================================================

def register_default_flows(manager):
    """Register all default flows with the manager."""
    manager.register_flow(BIRTH_DETAILS_FLOW)
    manager.register_flow(LIFE_PREDICTION_FLOW)
    manager.register_flow(KUNDLI_MATCHING_FLOW)
    manager.register_flow(DOSHA_CHECK_FLOW)
    manager.register_flow(HOROSCOPE_FLOW)
