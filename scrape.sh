# first get the missing person IDs from these CSVs:
# https://drive.google.com/open?id=1pQ6Q9HYnDo-aDfPannJIh2IN2pBkQmyR
# https://drive.google.com/open?id=1JQl0huUyhft1MJ62af4mvit1V3wd4SsX
# then make this request:
curl 'https://www.namus.gov/api/CaseSets/NamUs/MissingPersons/Cases/50435' > '50435.json'
# this downloads a JSON response which contains A URL to their thumbnail and full photo
jq '.images[].files.original.href' '50435.json'
