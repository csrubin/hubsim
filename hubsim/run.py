"""

"""
import random
import statistics

import plotly.colors as pc
import plotly.express as px
import plotly.graph_objs as go
import simpy
import streamlit as st
from config import Config, DataMonitor, HubEnvironment
from hub import Hub


def main():
    config = Config()
    monitor = DataMonitor()

    st.set_page_config(
        page_title="Hub Simulation",
        # TODO menu
        menu_items={},
    )

    def check_password():
        """Returns `True` if the user had a correct password."""

        def password_entered():
            """Checks whether a password entered by the user is correct."""
            if (
                st.session_state["username"] in st.secrets["passwords"]
                and st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]
            ):
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # don't store  password
                # TODO: Implement user privileges based on st.session_state["username"]
            else:
                st.session_state["password_correct"] = False

        if "password_correct" not in st.session_state:
            # First run, show inputs for username + password.
            st.text_input("Username", on_change=password_entered, key="username")
            st.text_input("Password", type="password", on_change=password_entered, key="password")
            return False
        elif not st.session_state["password_correct"]:
            # Password not correct, show input + error.
            st.text_input("Username", on_change=password_entered, key="username")
            st.text_input("Password", type="password", on_change=password_entered, key="password")
            st.error("😕 User not known or password incorrect")
            return False
        else:
            # Password correct.
            return True

    if check_password():
        st.title("Hub Simulation")
        st.markdown("---")

        with st.sidebar:
            st.image("hubsim/assets/Black_Orange_Wordmark_Lockup_DroneUp_sm.png")
            st.header("Configuration")
            st.markdown("---")

            st.subheader("General")
            hours = st.number_input("Operating Hours:", value=12.0, format="%.1f", step=0.5)

            randcol, rerun_col = st.columns(2, gap="large")

            with randcol:
                config.RANDOM = st.checkbox("Randomize", value=False)
            with rerun_col:
                st.button("Rerun", disabled=not config.RANDOM)

            # TODO: simulation run count, summary stats (when randomize)

            st.subheader("Resource Profile")

            numcol, _ = st.columns(2)
            with numcol:
                # Perhaps an "on_change" callback to set config object?
                config.NUM_PILOTS = st.number_input("Pilots:", value=config.NUM_PILOTS, min_value=1)
                config.NUM_DELIVERY_SPECIALISTS = st.number_input(
                    "Delivery Specialists:",
                    value=config.NUM_DELIVERY_SPECIALISTS,
                    min_value=1,
                )
                config.NUM_DRONES = st.number_input("Drones:", value=config.NUM_DRONES, min_value=1)
                config.NUM_BATTERIES = st.number_input("Batteries:", value=config.NUM_BATTERIES, min_value=1)

            st.subheader("Time Intervals (minutes)")
            config.PICK_PACK_INTERVAL_MIN = st.slider(
                "Pick-Packing:", value=config.PICK_PACK_INTERVAL_MIN, max_value=60
            )
            config.ORDER_INTERVAL_MIN = st.slider(
                "Time Between Orders:", value=config.ORDER_INTERVAL_MIN, max_value=60 * 4
            )
            config.FLIGHT_INTERVAL_MIN = st.slider("Mission Duration:", value=config.FLIGHT_INTERVAL_MIN, max_value=20)

            # TODO: Export data, export plots

        env = HubEnvironment(config, monitor)
        hub = Hub(env)
        until = hours * 60
        hub.env.run(until=until)

        fig = px.scatter(x=hub.monitor.delivery_times, y=hub.monitor.wait_times, color_discrete_sequence=["#ff6c32"])
        annot = go.layout.Annotation(text=f"Average: {statistics.mean(hub.env.monitor.wait_times):.1f} min")
        line = go.layout.shape.Line(color="#4e5556", dash="dash")
        fig.add_hline(y=statistics.mean(hub.monitor.wait_times), annotation=annot, line=line)
        fig.update_layout(
            yaxis_title="Order Wait Time",
            xaxis_title="Simulation Environment Time (min)",
            title_text="Delivery Wait Times",
        )

        st.subheader(f"Total Orders: {hub.env.monitor.orders_delivered}")

        st.plotly_chart(fig)
        st.caption(
            "<p style='text-align: center'; >If this chart looks 'random' then the hub is not under-resourced."
            " However, it may be over-resourced. </p>",
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
