![image](https://developer.nintendo.com/Independent_Server_Setup_Manual/contents/template/img/noscript.svg)

|  |  |
| --- | --- |
| [<< 4.7.3 ID Tokens](https://developer.nintendo.com/Independent_Server_Setup_Manual/contents/Pages/Page_238690855.html) | [4.7.5 API for Getting the History for Canceling User Authorization >>](https://developer.nintendo.com/Independent_Server_Setup_Manual/contents/Pages/Page_1222800966.html) |

[4 Linking With Nintendo Accounts](https://developer.nintendo.com/Independent_Server_Setup_Manual/contents/Pages/Page_126568335.html) > [4.7 API Reference](https://developer.nintendo.com/Independent_Server_Setup_Manual/contents/Pages/Page_1222798539.html) > [4.7.4 Account API](https://developer.nintendo.com/Independent_Server_Setup_Manual/contents/Pages/Page_238691342.html)

4.7.4 Account API

## Request Specification

###### HTTP Method/Path

|  |  |
| --- | --- |
| HTTP method | GET |
| Path | /2.0.0/users/me |

###### Request Parameters

| Item | Specification Method | Required? | Description |
| --- | --- | --- | --- |
| Authorization | header | Y | Bearer access token. |

## Response Specification

The response is returned in `application/json` format. If the request succeeds, the following properties are returned in the response.

| Item | Type | Required Permission | Description |
| --- | --- | --- | --- |
| id | string | - | Represents the Nintendo Account identifier.  Normally, this contains the PPID. For more information about PPID, see [4.6 NAID and PPID](https://developer.nintendo.com/Independent_Server_Setup_Manual/contents/Pages/Page_1222798523.html). |
| country | string | user.basic user.country | The user's country of residence. The format is ISO 3166-1 alpha-2.  The countries where a Nintendo Account can be registered may increase in the future as the service expands. Implement your independent server to operate without problems even if more countries can be set for this property in the future.  Note:  New scope requests are not being accepted for the scope of `user.basic`. |
| language | string | user.basic | The language used by the user. Indicated by the `Locale` value (a hyphenated value comprising the language code, represented in IS 639-1, connected by a hyphen (-) to the country code, represented in ISO 3166-1 alpha-2).  Note:  New scope requests are not being accepted for the scope of `user.basic`. |
| timezone | object | user.basic | The user's time zone. It includes the following information.  - id: Expressed as a string like "Asia/Tokyo." - name: Expressed as a string like "Asia/Tokyo." - utcOffsetSeconds: Value that indicates the UTC offset in seconds. - utcOffset: Value that indicates the UTC offset.  Note:  New scope requests are not being accepted for the scope of `user.basic`. |
| gender | string | user.basic | The user's gender.  - unknown (Not registered) - male - female Note:  New scope requests are not being accepted for the scope of `user.basic`. |
| birthday | string | user.birthday | The user's date of birth. The format is YYYY-MM-DD.  Note:  New scope requests are not being accepted for the scope of `user.birthday`. |
| email | string | user.email | The user's email address. If the target Nintendo Account is a child account, you cannot obtain an email address. For more information about child accounts, see the Nintendo Switch Account Guide.  Note:  New scope requests are not being accepted for `user.email`. |
| links | object | user.links.nintendoNetwork.id | Contains the information about the linked Nintendo Network ID.  - `id`: The internal ID (principal ID) of the Nintendo Network ID. - `createdAt`: The date and time when the Nintendo Network ID was linked to the Nintendo ID (UNIX timestamp).  \|  \| \| --- \| \| ```   "links": {     "nintendoNetwork": {       "id": "1799873081",       "createdAt": 1476857705     }   } ``` \|  If the user has not linked a Nintendo Network ID, an empty object will be returned even if authorization was acquired.  \|  \| \| --- \| \| ``` "links": {} ``` \|  Note:  New scope requests are not being accepted for `user.links.nintendoNetwork.id`. |

###### Sample

|  |
| --- |
| ``` GET /2.0.0/users/me HTTP/1.1 Host: e97b8a9d672e4ce4845ec6947cd66ef6-sb-api.accounts.nintendo.com Authorization: Bearer ey...   HTTP/1.1 200 OK Content-Type: application/json; charset=UTF-8 {   "id": "fdfdc610f849726e",   "birthday": "1984-10-03",   "country": "JP",   "email": "test+0001@example.com",   "gender": "male",   "language": "ja-JP",   "links": {     "nintendoNetwork": {       "id": "1799873081",       "createdAt": 1476857705     }   },   "timezone": {     "utcOffsetSeconds": 32400,     "utcOffset": "+09:00",     "id": "Asia/Tokyo",     "name": "Asia/Tokyo"   } } ``` |

If the request fails, the following error is returned.

| Item | Description |
| --- | --- |
| status | The HTTP status code. |
| errorCode |  |
| detail | Text describing the content of `errorCode`. |

[4 Linking With Nintendo Accounts](https://developer.nintendo.com/Independent_Server_Setup_Manual/contents/Pages/Page_126568335.html) > [4.7 API Reference](https://developer.nintendo.com/Independent_Server_Setup_Manual/contents/Pages/Page_1222798539.html) > [4.7.4 Account API](https://developer.nintendo.com/Independent_Server_Setup_Manual/contents/Pages/Page_238691342.html)

|  |  |
| --- | --- |
| [<< 4.7.3 ID Tokens](https://developer.nintendo.com/Independent_Server_Setup_Manual/contents/Pages/Page_238690855.html) | [4.7.5 API for Getting the History for Canceling User Authorization >>](https://developer.nintendo.com/Independent_Server_Setup_Manual/contents/Pages/Page_1222800966.html) |
|  |  |

---

CONFIDENTIAL