import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

# ---------- Config ----------
DATA_PATH = Path("data/foods.csv")

st.set_page_config(page_title="Pet Nutrition Assistant", page_icon="🐾")
st.title("🐾 Pet Nutrition Assistant")
st.write("Quickly check which foods are safe for dogs 🐶 or cats 🐱 and get recipe ideas!")
st.caption("Educational tool — not a substitute for veterinary advice.")

# ---- Custom CSS ----
st.markdown(
    """
    <style>
    /* Background gradient */
    .stApp {
        background: linear-gradient(135deg, #fceabb, #f8b500);
    }

    /* Center the title */
    .title {
        text-align: center;
        font-size: 2.5rem;
        color: #333333;
    }

    /* Round images */
    .rounded-img {
        border-radius: 50%;
    }

    /* Table styling */
    table {
        border-collapse: collapse;
        width: 100%;
    }
    th, td {
        padding: 8px;
        text-align: left;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title
#st.markdown("<h1 class='title'>🐾 Pet Nutrition Assistant</h1>", unsafe_allow_html=True)

# ---------- Demo Tabs ----------

tab1, tab2, tab3 = st.tabs(["🍽️ Nutrition Assistant", "📜 History", "👩💻 About"])

@st.cache_data
def load_foods(path=DATA_PATH):
    df = pd.read_csv(path)
    # normalize
    df["ingredient_lc"] = df["ingredient"].str.strip().str.lower()
    df["is_safe_for_dogs"] = df["is_safe_for_dogs"].str.strip().str.lower()
    df["is_safe_for_cats"] = df["is_safe_for_cats"].str.strip().str.lower()
    return df

df = load_foods()

# UI: species selector and input
with tab1:
    items = []
    matched_safe = pd.DataFrame()
    matched_unsafe = pd.DataFrame()
    matched_unknown = []
    species = st.radio("Select your pet:", ["Dog", "Cat"])
    ingredients_input = st.text_area(
      "Enter fridge ingredients (comma separated):",
       placeholder="e.g., chicken, rice, chocolate"
)

    if st.button("Check ingredients"):
        items = [i.strip().lower() for i in ingredients_input.split(",") if i.strip()]
    if not items:
        st.info("Please enter at least one ingredient.")
    else:
        # choose safety column
        col = "is_safe_for_dogs" if species.lower() == "dog" else "is_safe_for_cats"

        # find matches
        matched = df[df["ingredient_lc"].isin(items)]
        matched_safe = matched[matched[col] == "yes"]
        matched_unsafe = matched[matched[col] == "no"]
        matched_unknown = [it for it in items if it not in matched["ingredient_lc"].values]

        if not matched_safe.empty:
            st.subheader("✅ Safe Ingredients")
            st.success("These foods are safe for your pet.")
            st.table(
                matched_safe[["ingredient", "notes"]]
                .rename(columns={"ingredient": "Ingredient", "notes": "Notes"})
            )

        if not matched_unsafe.empty:
            st.subheader("❌ Unsafe Ingredients")
            st.error("⚠️ These foods are unsafe and should be avoided.")
            st.table(
                matched_unsafe[["ingredient", "notes"]]
                .rename(columns={"ingredient": "Ingredient", "notes": "Why"})
            )

        if matched_unknown:
            with st.container():
               st.subheader("❓ Unknown Ingredients")
               st.warning("These items aren’t in our dataset yet.")
               st.write(", ".join(matched_unknown))
        # Plotly pie chart visualization
        sizes = [len(matched_safe), len(matched_unsafe), len(matched_unknown)]
        labels = ["Safe", "Unsafe", "Unknown"]

        if sum(sizes) > 0:  # avoid empty pie chart
            fig = px.pie(
                values=sizes,
                names=labels,
                color=labels,
                color_discrete_map={
                    "Safe": "#8fd694",
                    "Unsafe": "#f28c8c",
                    "Unknown": "#ffd966"
                },
                title="📊 Ingredient Safety Overview"
            )
            fig.update_traces(textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)

    if items:
        st.session_state.history.append({
            "species": species,
            "ingredients": items,
            "safe": list(matched_safe["ingredient"]) if not matched_safe.empty else [],
            "unsafe": list(matched_unsafe["ingredient"]) if not matched_unsafe.empty else [],
            "unknown": matched_unknown
            })


# ---------- Recipe Suggestions ----------
@st.cache_data
def load_recipes(path="data/recipes.csv"):
    df = pd.read_csv(path)
    df["ingredients_list"] = df["ingredients"].apply(
        lambda x: [i.strip().lower() for i in x.split(",")]
    )
    return df

recipes_df = load_recipes()
with tab1:
    if st.button("Suggest recipes"):
        if not ingredients_input.strip():
            st.info("Enter ingredients first to get recipes.")
    else:
        user_items = [i.strip().lower() for i in ingredients_input.split(",") if i.strip()]
        suggestions = []

        for _, row in recipes_df.iterrows():
            recipe_ingredients = row["ingredients_list"]
            present = [i for i in recipe_ingredients if i in user_items]
            missing = [i for i in recipe_ingredients if i not in user_items]

            match_percent = len(present) / len(recipe_ingredients)

            if match_percent > 0:  # at least 1 ingredient matches
                suggestions.append({
                    "recipe_name": row["recipe_name"],
                    "notes": row["notes"],
                    "present": present,
                    "missing": missing,
                    "match_percent": match_percent
                })

        if suggestions:
            st.subheader("🍲 Recipe Suggestions")
            for rec in sorted(suggestions, key=lambda x: -x["match_percent"]):
                st.markdown(f"**{rec['recipe_name']}** — {rec['notes']}")
                st.write(f"✅ You have: {', '.join(rec['present'])}")
                if rec["missing"]:
                    st.write(f"⚠️ Missing: {', '.join(rec['missing'])}")
                st.divider()
        else:
            st.info("No recipes matched your ingredients.")
with tab2:
    st.subheader("📜 Your Search History")
    if 'history' not in st.session_state:
        st.session_state.history = []

    if st.session_state.history:
        # Button to clear history
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.info("History cleared.")

        # Show each past entry
        for i, entry in enumerate(st.session_state.history, 1):
            with st.expander(f"🔎 {i}. {entry['species']} — {', '.join(entry['ingredients'])}"):
                if entry["safe"]:
                    st.write(f"✅ Safe: {', '.join(entry['safe'])}")
                if entry["unsafe"]:
                    st.write(f"❌ Unsafe: {', '.join(entry['unsafe'])}")
                if entry["unknown"]:
                    st.write(f"❓ Unknown: {', '.join(entry['unknown'])}")
    else:
        st.info("No history yet. Try searching some foods!")

# ---------------- About ----------------
with tab3:
    st.subheader("👩💻 About the Project")
    st.write(
        "This project helps pet owners check which foods are safe or unsafe "
        "for their dogs and cats, and suggests simple recipes using available ingredients."
    )
    st.markdown("**Developed by:** Naushaba Azmi")
    st.markdown("### Vision")
    st.markdown(
        """
        - Help pet owners avoid harmful foods  
        - Suggest simple, pet-friendly recipes  
        - Build awareness with a friendly, educational tool  
        """
    )

# ---------- Footer ----------
st.markdown(
    "<hr><center>Made with ❤️ at Animal Hack 2025 by Naushaba Azmi</center>",
    unsafe_allow_html=True
)
