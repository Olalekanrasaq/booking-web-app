import streamlit as st
from datetime import datetime, timedelta
import json
import pandas as pd
import streamlit.components.v1
from streamlit_gsheets import GSheetsConnection

conn = st.connection("gsheets", type=GSheetsConnection)

st.title("Booking App")
st.markdown("---")

st.sidebar.header("TGA Booking")

selection = st.sidebar.radio("Request", 
                             ["Booking Calendar", "Book Apartment"])

if selection == "Booking Calendar":
    st.info("Dates colored red have been booked")
    # Adjust end dates in the booking data
    sel_apartment = st.selectbox("Select Apartment", ["-", "Upper floor", "Middle floor", "Ground floor"])
    if sel_apartment != "-":
        bookings = conn.read(worksheet="booking", ttl=5)
        bookings = bookings[bookings["Apartment"] == sel_apartment]
        for index, booking in list(bookings.iterrows()):
            bookings.at[index, 'Check_out'] = (datetime.strptime(booking.Check_out, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    
        # Convert booking data into JSON-like structure for FullCalendar
        events = [
            {"start": booking.Check_in, "end": booking.Check_out}
            for booking in list(bookings.itertuples())
        ]

        # FullCalendar.js with selectable dates
        fullcalendar_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <link href="https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/locales-all.min.js"></script>
        <style>
            .fc-event-title {{
            text-align: center;
            font-weight: bold;
            font-size: 2.2em;
            }}
        </style>
        </head>
        <body>
        <div id="calendar"></div>
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
            var calendarEl = document.getElementById('calendar');
            var calendar = new FullCalendar.Calendar(calendarEl, {{
                initialView: 'dayGridMonth',
                selectable: true,
                events: {events},  // Inject event data
                eventColor: '#FF0000',  // Set event color to red
            }});
            calendar.render();
            }});
        </script>
        </body>
        </html>
        """

        # JavaScript and Python communication handler
        streamlit.components.v1.html(fullcalendar_code, height=500)

        st.markdown("---")
        st.markdown("###### Booking records for the selected apartments")
        st.dataframe(bookings, hide_index=True)


elif selection == "Book Apartment":
    st.subheader("Book Apartment")
    name = st.text_input("Name of the Customer")
    address = st.text_input("Address")
    phone = st.text_input("Phone Number")
    phone = f'NG- {phone}'
    email = st.text_input("Email")
    apartment = st.selectbox("Choose apartment", 
                             ["Upper floor", "Middle floor", "Ground floor"])
    check_in = st.date_input("Check-In date")
    check_out = st.date_input("Check-Out date")
    booking_code = st.text_input("Booking Code", type="password")

    submit = st.button("Book")

    if submit:
        if booking_code == "0000":
            bookings = conn.read(worksheet="booking", ttl=5)
            # Validate if the booking dates overlap
            overlap = False
            for booking in list(bookings.itertuples()):
                if booking.Apartment == apartment:
                    existing_check_in = datetime.fromisoformat(booking.Check_in).date()
                    existing_check_out = datetime.fromisoformat(booking.Check_out).date()
                
                    # Check for overlap
                    if (check_in < existing_check_out and check_out >= existing_check_in):
                        overlap = True
                        break

            if overlap:
                st.error("This apartment is already booked for the selected dates. Please choose different dates.")
            else:
                # No overlap, proceed with booking

            
                book_dict = {
                    "Name": name.title(),
                    "Address": address,
                    "Phone": phone,
                    "Email": email,
                    "Apartment": apartment,
                    "Check_in": check_in.isoformat(),
                    "Check_out": check_out.isoformat(),
                    "Days": (check_out - check_in).days
                }

                # Convert the new row into a DataFrame
                new_df = pd.DataFrame([book_dict])
                # append the new user
                bookings_df = pd.concat([bookings, new_df], ignore_index=True) 
                # Update the spreadsheet or database
                conn.update(worksheet="booking", data=bookings_df)

                st.success("Room has been booked successfully!!")

        else:
            st.error("Invalid booking code! You are not authorized to book")