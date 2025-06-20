import lbc

def main() -> None:
    client = lbc.Client()

    # Paris
    location = lbc.City( 
        lat=48.85994982004764,
        lng=2.33801967847424,
        radius=10_000, # 10 km
        city="Paris"
    )

    result = client.search(
        text="maison",
        locations=[location],
        page=1,
        limit=35,
        limit_alu=0,
        sort=lbc.Sort.NEWEST,
        ad_type=lbc.AdType.OFFER,
        category=lbc.Category.IMMOBILIER,
        owner_type=lbc.OwnerType.ALL,
        search_in_title_only=True,
        square=(200, 400),
        price=[300_000, 700_000]
    )

    for ad in result.ads:
        print(ad.id, ad.url, ad.subject, ad.price)

if __name__ == "__main__":
    main()