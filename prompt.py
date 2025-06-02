def get_trip_plan_prompt(start_location, destination, num_days, start_date, end_date, budget=None):
    """Generate a detailed prompt for trip planning AI"""
    
    budget_info = ""
    if budget and budget.get('amount', 0) > 0:
        budget_info = f"""
BUDGET CONSTRAINTS:
- Total Budget: {budget['symbol']}{budget['amount']:,.0f} {budget['currency']}
- Please ensure all recommendations fit within this budget
- Provide cost breakdowns for major expenses
- Suggest budget-friendly alternatives where applicable
"""
    
    prompt = f"""
You are an expert travel planner with extensive knowledge of destinations worldwide. Create a comprehensive, detailed travel plan for the following trip:

TRIP DETAILS:
- From: {start_location}
- To: {destination}
- Duration: {num_days} days ({start_date} to {end_date})
- Travel Dates: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}
{budget_info}

Please provide a detailed travel plan that includes:

1. **OVERVIEW & HIGHLIGHTS**
   - Brief destination overview
   - Best time to visit and weather expectations for travel dates
   - Top 3-5 must-see attractions/experiences
   - Cultural insights and local customs to be aware of

2. **TRANSPORTATION**
   - Best ways to reach {destination} from {start_location}
   - Recommended flight routes or transportation modes
   - Local transportation options (metro, buses, taxis, car rentals)
   - Estimated transportation costs

3. **ACCOMMODATION RECOMMENDATIONS**
   - 3-4 accommodation options with different price ranges
   - Best areas to stay based on itinerary
   - Booking tips and estimated costs per night

4. **DETAILED DAY-BY-DAY ITINERARY**
   Create a day-by-day plan with:
   - Morning, afternoon, and evening activities
   - Specific attractions with brief descriptions
   - Recommended restaurants for meals
   - Travel time between locations
   - Estimated costs for activities and meals
   - Alternative options in case of bad weather

5. **FOOD & DINING**
   - Must-try local dishes and specialties
   - Recommended restaurants (budget, mid-range, fine dining)
   - Street food recommendations and safety tips
   - Dietary restrictions accommodations

6. **PRACTICAL INFORMATION**
   - Visa requirements (if applicable)
   - Currency and payment methods
   - Language basics and useful phrases
   - Emergency contacts and important numbers
   - Health and safety tips
   - What to pack (considering weather and activities)

7. **BUDGET BREAKDOWN** (if budget provided)
   - Accommodation: estimated cost
   - Transportation: local and international
   - Food and dining: daily estimates
   - Activities and attractions: entry fees
   - Shopping and souvenirs: suggested amount
   - Emergency fund: recommended amount

8. **INSIDER TIPS & HIDDEN GEMS**
   - Lesser-known attractions worth visiting
   - Local experiences and cultural activities
   - Best times to visit popular attractions (avoid crowds)
   - Money-saving tips and free activities
   - Local etiquette and customs

9. **PACKING CHECKLIST**
   - Essential items based on destination and season
   - Electronics and adapters needed
   - Clothing recommendations
   - Health and safety items

10. **ALTERNATIVE PLANS**
    - Backup indoor activities for bad weather
    - Flexible options that can be swapped
    - Extended stay recommendations (if staying longer)

Please make the itinerary realistic, considering travel times between locations and avoiding over-packing each day. Focus on creating a balance between must-see attractions, cultural experiences, relaxation, and local interactions.

Format the response in a clear, organized manner using headers and bullet points for easy reading. Make it engaging and informative, as if you're personally guiding the traveler through their journey.

Consider the traveler's perspective: they want practical, actionable advice that will help them make the most of their {num_days}-day trip to {destination}.
"""
    
    return prompt

def get_destination_info_prompt(destination):
    """Generate prompt for getting basic destination information"""
    
    prompt = f"""
Provide comprehensive information about {destination} as a travel destination:

1. **DESTINATION OVERVIEW**
   - Location and geography
   - Population and major cities
   - Official language(s) and commonly spoken languages
   - Currency and exchange rates

2. **CLIMATE & BEST TIME TO VISIT**
   - Climate zones and seasonal patterns
   - Best months to visit and why
   - Weather to expect in different seasons
   - Monsoon/rainy seasons to avoid

3. **TOP ATTRACTIONS & EXPERIENCES**
   - Must-visit landmarks and attractions
   - Natural wonders and scenic spots
   - Cultural and historical sites
   - Adventure activities and outdoor experiences
   - Unique local experiences

4. **CULTURE & CUSTOMS**
   - Local traditions and customs
   - Religious practices and etiquette
   - Social norms and cultural sensitivity
   - Festivals and celebrations

5. **PRACTICAL TRAVEL INFORMATION**
   - Visa requirements for most countries
   - Health and vaccination requirements
   - Safety considerations and common scams
   - Tipping culture and bargaining practices

6. **COST OF LIVING & TRAVEL**
   - General cost level (budget/moderate/expensive)
   - Average costs for accommodation, food, transport
   - Currency and payment methods accepted
   - Budget travel tips

Keep the information practical, accurate, and helpful for trip planning.
"""
    
    return prompt

def get_activity_recommendations_prompt(destination, interests, duration):
    """Generate prompt for activity recommendations based on interests"""
    
    interests_str = ", ".join(interests) if isinstance(interests, list) else str(interests)
    
    prompt = f"""
Based on the following preferences, recommend specific activities and experiences in {destination}:

TRAVELER INTERESTS: {interests_str}
TRIP DURATION: {duration} days

Please provide:

1. **TAILORED ACTIVITY RECOMMENDATIONS**
   - Activities matching the specified interests
   - Unique experiences not found elsewhere
   - Both popular and off-the-beaten-path options

2. **EXPERIENCE LEVELS**
   - Beginner-friendly options
   - Intermediate challenges
   - Advanced/expert level activities

3. **TIME REQUIREMENTS**
   - Half-day activities
   - Full-day experiences
   - Multi-day excursions

4. **SEASONAL CONSIDERATIONS**
   - Best time of year for each activity
   - Weather-dependent alternatives
   - Indoor backup options

5. **PRACTICAL DETAILS**
   - Booking requirements and advance notice needed
   - Equipment rental vs. bringing own gear
   - Cost estimates and value for money
   - Transportation to activity locations

6. **SAFETY & PREPARATION**
   - Safety considerations and requirements
   - Physical fitness requirements
   - What to bring/wear
   - Insurance recommendations

Focus on creating memorable experiences that align with the traveler's interests while being practical for the given timeframe.
"""
    
    return prompt

def get_budget_optimization_prompt(destination, budget, duration, priorities):
    """Generate prompt for budget optimization advice"""
    
    prompt = f"""
Help optimize a travel budget for {destination}:

BUDGET: {budget.get('symbol', '$')}{budget.get('amount', 0):,.0f} {budget.get('currency', 'USD')}
DURATION: {duration} days
PRIORITIES: {priorities}

Provide detailed budget optimization advice:

1. **BUDGET ALLOCATION STRATEGY**
   - Recommended percentage breakdown by category
   - Priority-based spending allocation
   - Essential vs. optional expenses

2. **COST-SAVING STRATEGIES**
   - Accommodation money-saving tips
   - Transportation cost reduction
   - Food and dining budget strategies
   - Activity and attraction savings

3. **VALUE-FOR-MONEY RECOMMENDATIONS**
   - Best bang-for-buck experiences
   - Free and low-cost activities
   - When to splurge vs. when to save

4. **DETAILED BUDGET BREAKDOWN**
   - Daily spending estimates
   - Category-wise cost projections
   - Emergency fund recommendations

5. **ALTERNATIVE OPTIONS**
   - Budget alternatives for expensive activities
   - Seasonal pricing considerations
   - Package deals and combo offers

6. **MONEY MANAGEMENT TIPS**
   - Payment methods and currency exchange
   - Avoiding tourist traps and overcharging
   - Negotiation and bargaining strategies

Make the advice practical and actionable, helping the traveler maximize their experience within budget constraints.
"""
    
    return prompt