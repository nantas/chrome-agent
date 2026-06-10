4.7.4 Account API


# Request Specification


###### HTTP Method/Path


| HTTP method | GET |
| --- | --- |
| Path | /2.0.0/users/me |


###### Request Parameters


| Item | Specification Method | Required? | Description |
| --- | --- | --- | --- |
| Authorization | header | Y | Bearer access token. |


# Response Specification


The response is returned in `application/json` format. If the request succeeds, the following properties are returned in the response.


| Item | Type | Required Permission | Description | |
| --- | --- | --- | --- | --- |
| id | string | - | Represents the Nintendo Account identifier. Normally, this contains the PPID. For more information about PPID, see 4.6 NAID and PPID . | |
| country | string | user.basic user.country | The user's country of residence. The format is ISO 3166-1 alpha-2. The countries where a Nintendo Account can be registered may increase in the future as the service expands. Implement your independent server to operate without problems even if more countries can be set for this property in the future. Note: New scope requests are not being accepted for the scope of user.basic . | |
| language | string | user.basic | The language used by the user. Indicated by the Locale value (a hyphenated value comprising the language code, represented in IS 639-1, connected by a hyphen (-) to the country code, represented in ISO 3166-1 alpha-2). Note: New scope requests are not being accepted for the scope of user.basic . | |
| timezone | object | user.basic | The user's time zone. It includes the following information. id: Expressed as a string like "Asia/Tokyo." name: Expressed as a string like "Asia/Tokyo." utcOffsetSeconds: Value that indicates the UTC offset in seconds. utcOffset: Value that indicates the UTC offset. Note: New scope requests are not being accepted for the scope of user.basic . | |
| gender | string | user.basic | The user's gender. unknown (Not registered) male female Note: New scope requests are not being accepted for the scope of user.basic . | |
| birthday | string | user.birthday | The user's date of birth. The format is YYYY-MM-DD. Note: New scope requests are not being accepted for the scope of user.birthday . | |
| email | string | user.email | The user's email address. If the target Nintendo Account is a child account, you cannot obtain an email address. For more information about child accounts, see the Nintendo Switch Account Guide . Note: New scope requests are not being accepted for user.email . | |
| links | object | user.links.nintendoNetwork.id | Contains the information about the linked Nintendo Network ID. id : The internal ID (principal ID) of the Nintendo Network ID. createdAt : The date and time when the Nintendo Network ID was linked to the Nintendo ID (UNIX timestamp). &nbsp;&nbsp;"links": { &nbsp;&nbsp;&nbsp;&nbsp;"nintendoNetwork": { &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"id": "1799873081", &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"createdAt": 1476857705 &nbsp;&nbsp;&nbsp;&nbsp;} &nbsp;&nbsp;} | |
| "links": {} | | | | |


###### Sample


| GET / 2.0 . 0 / users / me HTTP / 1.1 Host : e97b8a9d672e4ce4845ec6947cd66ef6 - sb - api . accounts . nintendo . com Authorization : Bearer ey ... &nbsp; HTTP / 1.1 200 OK Content - Type : application / json ; charset = UTF - 8 { &nbsp;&nbsp; "id" : "fdfdc610f849726e" , &nbsp;&nbsp; "birthday" : "1984-10-03" , &nbsp;&nbsp; "country" : "JP" , &nbsp;&nbsp; "email" : "test+0001@example.com" , &nbsp;&nbsp; "gender" : "male" , &nbsp;&nbsp; "language" : "ja-JP" , &nbsp;&nbsp; "links" : { &nbsp;&nbsp;&nbsp;&nbsp; "nintendoNetwork" : { &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; "id" : "1799873081" , &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; "createdAt" : 1476857705 &nbsp;&nbsp;&nbsp;&nbsp; } &nbsp;&nbsp; }, &nbsp;&nbsp; "timezone" : { &nbsp;&nbsp;&nbsp;&nbsp; "utcOffsetSeconds" : 32400 , &nbsp;&nbsp;&nbsp;&nbsp; "utcOffset" : "+09:00" , &nbsp;&nbsp;&nbsp;&nbsp; "id" : "Asia/Tokyo" , &nbsp;&nbsp;&nbsp;&nbsp; "name" : "Asia/Tokyo" &nbsp;&nbsp; } } |
| --- |


If the request fails, the following error is returned.


| Item | Description | | |
| --- | --- | --- | --- |
| status | The HTTP status code. | | |
| errorCode | Value | Description | |
| invalid_token | Error that occurs if the access token is invalid or has expired. | | |
| insufficient_scope | Error that occurs if an attempt is made to do something for which permission has not been granted. | | |
| detail | Text describing the content of errorCode . | | |


[4 Linking With Nintendo Accounts](../Pages/Page_126568335.html) > [4.7 API Reference](../Pages/Page_1222798539.html) > [4.7.4 Account API](../Pages/Page_238691342.html)