import lbc

def main() -> None:
    client = lbc.Client()

    result = client.search(
        url="https://www.leboncoin.fr/recherche?category=9&text=maison&locations=Paris__48.86023250788424_2.339006433295173_9256&square=100-200&price=500000-1000000&rooms=1-6&bedrooms=3-6&outside_access=garden,terrace&orientation=south_west&owner_type=private",
        page=1,
        limit=35
    )
    
    for ad in result.ads:
        print(ad.id, ad.url, ad.subject, ad.price)

if __name__ == "__main__":
    main()