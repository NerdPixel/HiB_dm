import numpy as np
import requests
import json
import pandas as pd
import matplotlib.pyplot as plt


def create_url(query, searchType, type, pageSize):
    return f"https://product-search.services.dmtech.com/de/search?query={query}&searchType={searchType}&type={type}&pageSize={pageSize}"


def get_responses(product_name, ):
    payload = {}
    headers = {}

    response = requests.request("GET", create_url(product_name, "product", "search", "50"),
                                headers=headers,
                                data=payload)
    f = open(product_name + ".json", "w")
    f.write(json.dumps(response.json(), indent=4))
    f.close()

    return response


def clean_up_data(response, filename, filter):
    df = pd.json_normalize(response.json()['products'])

    columns_to_not_drop = ["gtin", "name", "price.value", "basePriceUnit", "basePrice.formattedValue",
                           "basePriceQuantity", "netQuantityContent", "price.currencySymbol"]

    columns_to_drop = list(set(df.columns.tolist()) - set(columns_to_not_drop))

    df.drop(columns=columns_to_drop, inplace=True)

    df = df[df['name'].str.contains(filter)]

    indexNames = df[df['basePriceUnit'] == 'St'].index
    df.drop(indexNames, inplace=True)

    mask = df['basePriceUnit'] == "l"
    df['basePriceQuantity'][mask] = 100.0
    df['basePriceUnit'][mask] = "ml"
    df[['basePrice.Value', 'basePrice.currencySymbol']] = df["basePrice.formattedValue"].str.split(" ", expand=True, )
    df.drop(columns=["basePrice.formattedValue"], inplace=True)
    df['basePrice.Value'] = df['basePrice.Value'].str.replace(",", ".")
    df['basePrice.Value'][mask] = df['basePrice.Value'].astype(float)[mask] / 10
    df['basePrice.Value'] = df['basePrice.Value'].astype(float)
    df['price.value'] = df['price.value'].astype(float)

    df.sort_index(axis=1, inplace=True)

    df.to_excel(filename + ".xlsx")

    return df


def plot_anzahl(genders, df_genders):
    plt.style.use('ggplot')

    n_products = list()
    x_pos = list()
    for i, df_gender in enumerate(df_genders):
        n_products.append(len(df_gender.index))
        x_pos.append(i)

    plt.bar(x_pos, n_products, color='#b9c997')
    for i, n_product in enumerate(n_products):
        plt.text(i, n_product + 0.1, str(n_product), ha='center')

    plt.xlabel("Geschlecht")
    plt.ylabel("#Produkte")
    plt.title("Rasierschaum Rasiergel Rasieröl Rasiercreme")
    plt.xticks(x_pos, genders)
    plt.savefig("anzahl_produkte.png", dpi=300)
    plt.close()


def plot_preis_100ml(genders, df_genders, marker, colors):
    plt.style.use('ggplot')
    means = list()
    x_pos = list()
    for i, df_gender in enumerate(df_genders):
        means.append(df_gender["basePrice.Value"].mean())
        x_pos.append(i)

    plt.bar(x_pos, means, color='#b9c997')

    for i, mean in enumerate(means):
        plt.text(i, mean + 0.1, "{:.2f} €".format(mean).replace('.', ','), ha='center')

    for i, gender, df_gender, marker, color in zip(x_pos, genders, df_genders, marker, colors):
        median = np.median(df_gender["basePrice.Value"])
        plt.plot(i, median, marker, markersize=16, color=color, label="Median " + gender)
        plt.text(i, median + 0.2, "{:.2f} €".format(median).replace('.', ','))

    x1, x2, y1, y2 = plt.axis()
    plt.axis((x1, x2, y1, y2 + 1))

    plt.xlabel("Geschlecht")
    plt.ylabel("Durchschnittspreis pro 100ml")
    plt.title("Rasierschaum Rasiergel Rasieröl Rasiercreme")
    plt.legend(facecolor='white', framealpha=1)
    plt.xticks(x_pos, genders)
    plt.savefig("durchschnittspreis_pro_100ml_produkte.png", dpi=300)
    plt.close()


if __name__ == '__main__':
    genders = ["Herren", "Frauen", "Divers"]
    colors = ["purple", "yellow", "blue"]
    markers = ["<", ">", "^"]
    filter = "Rasierschaum|Rasiergel|Rasieröl|Rasiercreme"

    gender_responses = list()
    for gender in genders:
        gender_responses.append(get_responses("rasierschaum " + gender))

    df_genders = list()
    for gender_response, gender in zip(gender_responses, genders):
        df_genders.append(clean_up_data(gender_response, gender, filter))

    plot_anzahl(genders, df_genders.copy())
    plot_preis_100ml(genders, df_genders.copy(), markers, colors)
