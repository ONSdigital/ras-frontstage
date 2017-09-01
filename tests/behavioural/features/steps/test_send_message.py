import requests
from behave import given, when, then
from flask import json

from frontstage.views.secure_messaging import headers
from tests.behavioural.features.steps.common import is_element_present_by_id


maxtext100 = 'lA4qe9NwQ5jO90Kkx30xf7Qjwcl8argK5IyJKutxUv6RlraTzwPSb2ka4XJ7TOJMCZyGgk0fCx8lLnOOQC3uJTBtfCiatbwvGNaZV'
maxtext10000 = '6OCGoxGt7ESVA7WkET3cnTUswEI1RzXNmRKAx6RiahrCnH9ywqgzRvBHIXIsFBUDAnOSvTCfEmpaCtahwTmD79wacI2acKLZhGm3zbV34H0mCH8Fy8aOhXr9Byn0Bqz6KWzrTJjWMrZZGYXJc7e5FzTnbsojttvJlvf3UVwH3hppAlet4tDWwGHwnF1j9EyygrY6G6W4Ao37fgLjZHO1ejyczf7PTjIXQMRMaMIeZB1fGe7LjP2SKk2Yyk8MEzLhG5JoAaeNpkaasqO5sQuTm3XIPzrt6fA77aQoZEJj4zGphaL4eUhG9NmGgKWitugh5qIHV1rtxRB1O6le9comRhbmA6cciDCgamiA6zTR5hrVCCoGUzEH1bT9bZuY8R7FbcDrfMCPBI2B5XZR9trxBylgXE9eKZZfjBXAKwM9D1Yeumaqbkf0sD09rVcLXgPKabKGMgWJfijUGRYhf9aBa54HocW4jsf4Jy68NB8w0i9mKMAi8Dh0CwbBl8tAZkESafuK85mKyejEfkBc7jxgn8rx5vLixw3cPth6WneLQZeI7RI5obkzJ2uvYXwwZO4rDkMJpR6qJKQW7DAbLP4zjwgtSjcpKiAbfRlkLBj9UbyiDgQpPgnQp6nj8wlIqHZ5xEIkgWjExVmqJMMO6ebuFkFLxoomZiV3e3QiLTKaXxL0lTQ6fRFrSmQlkBVfsyiSR5cPqV2agB9vLsFe7UMrv9DcKsYOGbagCStC3KvUQ2gVzp7y2KObPUpSPSuT1weONEMNGzzjST2DjCZZYl2OtooskTAgtC9vpMY5A9QxWsIBL207g7NiULgprw9KbRGZHYPignJ62Yz9nbs1a2ocSwTUl6K0eUjBaczQsqUPnNntjIni9CehHaNYHHxETYG1CPJ1WB5jNhQGQDu5parpDnbKkzePh5Qhcn9Lsa08MB76pSHVbOP3EoAISRgT3rprWFX4jxto00WID1NcKNtRVScn6S8UGXy0Jr0b3tkTPbStFcIJr4HnIfpW34cMQnyEriQFC2GlWPVMyvwZlu9HUAQ6gAfvDpTKZWjiEYCFTMNyDQDanoyH73PGHEmvxMqRiQuJX9skxaMoEGAE8A91zp4JNU2RMFGsWjoosCPTNlufv9ECOr2x3VlzIxrBxIT3xn5WFaeTPiG8FIODueyA0AsB0bWmz4t0yMJpsmrjcFabOM1Q705t3WGsy0C0FxTrAHiIhjnTw5ZHXtpGNnEfOEsXr9we5h6MKJhNaX7Rty65PnHC9cnsu3wWpjzYVQ7fJPzzeF4hEj6poWMEaw95SjNCnGnqfz8XZv1w4s2YDhcsA5jmLnoQNqeJ1u6Pjm8eLRJ10w2v4fyzFJnZi8DIXO5FXsSZXOMV4AFXOk3rp6XQGFn7fpxi8S4bkJbkAUOakvcBYjH9YhFA4M7MoZu7RJ1Qn8T6hS7nRYHEA6XSLLx7EcXs1MPMAiDUJCFhJXFZHmQeYboruBEko3FlvJtMgWGRsxKWaefJ8DIpRKuta4NpUJwfX5PwWv7uEPCgCeWiRbzwttkAgn9ES9Jz5ibBVAn9oKUjkXB6nNDoWnBU6EPj9Ak1jDg5g4bGaP0VI8e9ctFIo4LhCl3GFNNRbErgCkQbM0t5sH1OZjYigfutHDIqvfI3iIg3XV89pbhRuimaVzDnrMIQU7BYmILPNAPTcLz30yP6ppSFQEwIQYUaXBuHxWXLFFmTDh3PGFvCm6tD2Fa9G0jYtU4HINs5VDFemZarwYDHw2qxDzUyKL01mXtT5ni0U71paF6FCAPBC7WmfCLyEl07XD9wnK3tJOslVQITAcxuEA60Lah6zhyDSapnslyb77jz1m0ALxPQsUiqv3BQJkRptrfDEaxte1aSs1C1h5OiU7Gw4FvDkFRYnAOTThiKDnkSPXeQHyeUhsvHYXYQDhz2ejxzWuhDS06kaGReRfwoOpP5B6vITDQhGB3EcuK2UnwqVRgKyw0uceIyHQE46SO66yqg0rlZAuhPmR1N9eu3AMvBctqK2Pcp635UD9uoLrOwqiwrEA185wUlZuETtTD3n5MnY4GprAhu1OxUmVxk12ttO9bySTeS1nvlJ8rJcI3gjyQ1RPKesmcCpLjrPrI1zNmx1kyTrQr7z66TZrGIwBhze4UMUj2z2RRgr8pj6ZB96NanS3y9hWXfp8LjpCuYnsuYJUFGhC91DZH3zNKpvYQy7QCNFzbSQU38jPy03Fi3wf5LEcaGtGH2HanQVJumjYqBV2OzYP4GOgbbkY84E9gaOMtkZRR5w3YXzV9jkCMo9jXuES53l9Koq89gzULIo69T9SoLQpzKGfMQbChUfL0OrAlFnGyZOSYU1LDnzyx6s63InUtFj5gTfBxFSw47CgsPRRua3NyhBwFqofGZ9Fuq3XZhJfS7tCXXcjTVFCulYNMN6ltiJQWPCPuWKU6bv93zPbvzU4muJcI9nbXhAuzZ9gqN3zi9O6CxB8mMz0AjPeO3fvAY0YsnggZU4sICJL58yxtJR0sJjiIaHZjUcBNcJ3UZWQgK98zoDyL2u8kIPom3LH3C0BgX48K5qxiGNuZqFuhts1xqQO0yA0bV5csP77DD9lCTRB6NL0pQwEEnEJbBRKFuqpKuJBL4Ub4tC10FCT79cozKYLEBy4MRPVIIxCaSx8P3JFjT2hPYeNo0AVEYsHvPeVssSpguHFb7tJbUJJamA8gqz9NnRXVhbvTyDlGflzAVIThQO85lzZCvGRBEosQ3fJopMoqRNkgBe0IM54rSgh1LFKENSJSzRx8F9xvj69q8skZ7zu12OZUi58Nm3kfqeCL75E8piQxipsmrCL63rRjbKOrhNJnSe2U5Ou56iOwTWp2Nqfnym04Q7PC5ggx10sfQ9ERWpZK2ogArX2rTl2LNECFE5USvHBQhtJwMliO2KTmqg4irIrY5qFWSvQ1PotWgAur1lwZFai88aMuWrnE61YVCWXkEmi3ipYnXqkv8VeJ9apqFiVAy56gLLrrWjKfwAyy0rrMMVsMLuEtaK7V6ucE29JloGG363pcmH6vpXQ3bFC6lgb4fLIcQVwqq7ywBfTevv1ajCaOhnrBxq6VfQZLIZ6xIEyVF5KKcQXv2Z6rbqpCqOYAEvJ64lNUBLBZuACf2a071qUka13V8eV04iM8BPhWDSpf1Wc0Tbi6gUAR5IvLRip20hKBqBLbl0xIqoBMOu6C6XSxk9ZsVcX7yuyEsHviu32AFSlBoB85s19QJp4I582A2NZR291BWElLbWPEQmSl7bPD9y8eI4VOjHokF60q0KOhSRH6jg1t4fTv4SZBfEXEhizoC65ESIX5YRhwRoTvv4EzYlStV3sXFVIiaEP7T8GixNbyVnbpWby8LCNQIIHPsN9DgesHLgP2lQm2luPzbiyRKkGzSKqPIv98ZuWSGY6zq3r9hz7G3xfmfVbBjRt6WlzCvpy7J6fVHlKyN7Y4aRTpnYa4giJ7WxgDG7a4EltaRP6zwmEO8bwsNf1AoJX9stMww8CvYmuK0XZNsvn4C6JvNzNF0x5Tf6m0M2MY8F4lKsuzCPmKbtwmSJgZQqXytlsAirQvGzPsHQL6TjxQHvabMDs9VXggAAHvh2l5z8EMQq4y7rcVP3QRoXo6tKSw1As2C3tnByDcnHMsbUolEfNVHrEgE9qZt4HUwbJjBIYNR1oj4t13RBaHfX8WgGmgJsZ4uRQ9al3Fb15y1IhLVQbUsneoxh5bl45yOeX1G4NHCZwvL9P90ao16CUZAFE4tpxFfWwRsc6JuMVtrXD2ekQAgK3tt3gZZwwr6JVzkJNxR2PSN0aBJVRcJOH042PbsMXw0rGFL1CfKpGfxi8UyhJGXrIAg3s8xn03GMvxQ7TtKlO5TZmJOxQJC5NLHo5hDyjFlmNKU7XAvnS5zFmBOsS6pFD7iGRSUVOBgVQnz7bvD97Xg3u475vO4ZO7H7hvD4UBUb015aLNJNB9ZFYRkrDc7QwJR1fGgzFW5PDUOT2Z1MOzGW6YytSQC3zQi1fjJ5IEN9ieDiVQjc9q7jQIk0qajvnBxRYEena3soBc5RlCSBP6CcWcGhA7r1DJNyVopnJrw53LVBtW5DJ18Q1IEXiB1XmMHPhAPyVSRkoV6L2acKQtzGDKRclRJJTfoH0VUmaKggU6rKl45jz1grDtBOOGoCYk0qEUEOQFAwuZMtLI8CObEvSssy5MWR3QGQfOPk32i5GbCtOv02W8AQFCfM2BNLmPzcqbbVZ2COZOY79i5mntgYeaE8yq4ugJIbfNMbbqHHFO3Puy3U2Cnl3qWLrhgYz5eAhWkcp2erbA4Y1csQVSP1TtoXP5QIt2jvO9Awy5HeG30qu3NJ4KSvyK6qW2qtUfCsv7mQrUYmm61uMHCRVlCWO6UrX5nma6RYkFcbeDav26e2YxGjArggs2okQobaO3jOmZy528RgmnJhVit7AUOYsjxBe0cM7nV0E6s8UJ8HIKQO07258f50gXyiXFBxhgYWuP4HcE74SbImbbQANqh12lfEpg3hYOiW4wsHeU2RfbvNfZbUG8sSR3qg7YXn7vP8GQD4LhXJpn8mESVIh5t4D1SkyC7TaBG5jwhvlUft3qhM2SrsmbCDy9XyH0ZAU0U42jebN59bEXoX15qHkXUDnuFZT2usMVCHBpyVxbnu5yoQ1Ra1Sbx8NXWGiJTbJ0Tw2FPLoETb2MvKEyUwWREBlKgxV32gK4y9g4Z0xbewrCyJHjR00OnTmmB12NIvZk0xLzjRurXkIWLvJezFSNvvwL4kWGNIRfvBUYsYLHK8uxtZAHFFNjaMP4NuqGEXwBotvEFEIXU3hrt8ihFP8L5hIxVxhtOqEi1zEyn7fsUhvShaYqZmP0r0bAj0UyETHro82CQWFMi9FUZZL6phPSD8sNQAHWPFtwzH2jJimPIOraJsyzF8BjZg67HwL8qBAu7gK1DlvOVi7XEI2PqznnRzQh3qPBq6IYvTf8bXhUNgbjfbp4G16GXHsZvAQiVsoLTRpJrzg6JorR0alqyiTvFNZ8DgRG9f31wv4egzUiCG4FknN8okOrMPMRwADtjBbS5R9ptw7fMbxhAWteFlSXYRAAqeKVAmR8kchCeUDkUUXzz7RvsSyqpuMx9pIaXzRENm34kBvIWLn2AouvGQO1gDt5JZaixsgYf4T4uptvtBCNLf3C4PfwQUPAOXvyPN1lBexBkxN4yNG5VFqABZOMuGa8ItgQZeSfiaPkgKGuUlzri3GlTjRYRNFS6NHviSmmBljjsNCTfEXrTCNNWtE2DatvkJs3VNRJuIufC5q1JIDT5Q6nZP6oS9RatGeuMbqcgHi79Qoxo52o2eR94M45M9vFJt4U0TprP7tRbbOLww290fbW3cuUxpiyfsjjNuaYksSEUMTVggUG73kntjFYx9pzNNVzMhWM6l2exYkirq1QFqluuwNHk1qGgrJTntomyS5hXofVRjLY53nk2a0HgiDaF4kBCIpyglSu9NwHBwecgI9sG3yRSuwgSTh1PuUqKvT9I94bWT5qgyuVlaNfhlKK5GYmEYweccpJam5wL6P6ah0eypFKzqPECgCkGZ9UARX7aVtPvIAoWX3g01EFHTSwqjtuJq7JA2CWxRAeTnxmSSPAuuaDhEgxuz14c4lBZlyQyEEinTN8cjVSTZFlho8rp8Il0RElcDCwXjfoV60PORo2DbDMpP2sYzkjhvo37h7VO6cBDb96AEuJLbh7UZr036gyo8sPFyYVrX39gOTfyv1GHgkbniJ1iGAMGyP25FxcQkw3KQKBkM4ym134iQ7xGZnm6XuXFFmXw3mYxrmfQXXTc7BNQAsN07n1ZnGn4NBwerZLIlE4Rffe0CZyCj1nBGW02CucrI0n5mqpfT9TOWziaPTCCvVHZCRva4pUCQak4h4FTVD1EJSTMzmkc7p0VFv6JaGCm1JCuRAxq64HskIE5zkJJFZYpsWylvKuC51JTT3G3lyPK2uzHOgiTqqqbT3VKMrZ3RvYsOPFzMLwO4guZZMmTRX3ODCpRHrUnommXJG6xCnjLx0RJInvf3hyJT3uhrj5Zk1ariCiIk32TBG2H5q78lcu2p5762Ohhbo23sEcUaSGA8QOFvzMpG5szj4uoyj99CFnSTnP8Ta5G07lW8ceSnWSkocqvCy8mN5Jn8F1KNFs7RAz4SpLhkMcVmrea0QggVUfuzww2QlfJE3Umr63llpOPoNNMgCAmBMvTa6gk9V9qvFbpmVVR5Z0nYJ5GYl1aqCJxDArgWWVAepxbJi48XIPfr7rvbInnqhtbTxlpmteDVu0GiYWGqoLak50GFybW3Ce8zLiqIVLA8ffXUzMuStZV30qfTfEUCqRx8N1TJg6axosZLYUJfGWSqULP91SG3SWzzqchJUNqg9xk0prov57r92KWsm2gXfnC2Q8WQ3FmcyhPN6CHeHuJfO6RTiR7OL1967VfnThsLzu2IyYA9EPFnnEWuqNjxuLMFcPKRLJCDDp0ECfYAAFqWlAll9bCkPruKbNtfYeYYQokrP5v5okDbnpAgbDW0oZ4pOnWHomy4bsb84xTIZ1wzDPwoMO50BgozEuAwhF9tNpVoeym6SkErL940DWrFHb1e82PBbkj71AlZloLsclf9tUAOcIszUm0za8wEOHFJNHFqm7QhfW15J9F97YutUEEQlR13s4bRivOPeJpcebDwoFPvfU0gozUojTZ1hC3R8EwvLosY2piMHLOPZ7UG3eAkxLfa4wMsmfV578GXaGYavCi9Xq1Hm0I0cP6uE2zIi5R4yqKQEY3SX4LPTMoQeDuqPNVU8nc8nBnVVhmcs7s9LIZkpRLut3LKI7UOkh3xWe1HRUot2EMNFfG952J5I7ukZTLQLFvU3rp1Yg9g0r227pAjG7IIRF5NyAja0GMnmjk5ZEzt682Qgtz7uJYMNZjWDsLxcCNJcP453nn9WiyinfqJw3YjUhXSNYfi3C8Hq5J9xRvN88oYASvbkNpnYk81VF0MohXU1Uz5WpiGrhnZ62lRYlNhyqgbI7vCIGM7GJqHClZiDfYZq6WYESZ3cVO8g3olpR0LoDCW9N6UhKCnPFEKhwc15i8Yi0XHrVGMrwLaCbnqtx4tKzRV0zVlyLDseQ45KVyUznIE428YwRycvjVET2fwoebwYycoVHsa8OBPwjGDmjtmZ8XWAn2Pckky3gWz0yFFTNufL5NDTzLHHllJLlI9rCHtSQt0C8wmcHvhEsZt5kQvveqEU4CGkWR2ac1PkrPgjmLJvi6ytIxNb1ZG5xWNxCPss6qFQyQ39XKfVeMoHg03fso2R65In69ArwbFZjfOYke8P8c1QzCNFmZQiyQBLgLc6BBFZyvLSG6LxfFUq3A7TREvEXyq95Be2rrlDx5qQStyUckS5SUPR0P6RcMgOxx7wZhiwN3ObHn15M5vSuzpYP9n6um32R7JlDh5UgqtgZjXKSDmjxpwI6NVlUpJbMIpsKnNJ3L2ljeT1CADJgejuaRU9LaTpaLDz06aAZv7IZDFzvCOa15AtnQk4SQluFyOl5kXn2LBDyIygukOAAYqsU53eAafa5ILDNZB1eQKJqtJanhgt8GmSBp1m0NcsMrX8GJ7cBoovA3egG9VrvbUz1S7estnoRBKrCLAS4HU7VhObZHZ1g7ccwLT7u2ZVYrRQ9fhkXm24ngIWmqgbblQmxlj5tFsnpiLIAmZB69QFSnkspSkbnU96P3asS46199GrhshMq8of0FIYoWyPNnBn5r7cZvZ2Szqvf8SVUmJ2rzRwnOf7brymUXuorgE3gWyytF0m1fDTvqXCJGYRzeMYfi7ioAK2KukR5XhyUAkw578K8AncVYCceh6FQqceYh5WKz0OnUpbK94HjiQyOap1fRa4N8nk79UE6ATWAMf6lCArBoxKgaotfsHrazoQ6ZKpjhA8JoyINNTTInLDbVC3lwjs4z9W4fkROUeZ8oPZXvOqsTPumJDt60IZ53XhZ0ADIU1jyuDaeAONIJcyv6qL8R0ID0MHZ89OH38qypytMED5BrrEGFAbpjbXwaLfbCr7z6SBR3b2GJRGgBC91G3ZpxaA0PHOqw0E73KnikfheOjeJhtt86smv6pOJD78qtPVUrMP9rUku0nImPNCZSL7PYLj1cQ7PaSzhMRrvPFZZyYpwJ2FvRvOpbBciYqQsjBXjGDfXMiiPk5Ff6B7pM1v6Xc2D8OIubY2H4whqj39H8UADDCoVNqS5hZU2GIt7focWoZg0UBMGUIDAz9AV8USMzTbOKyePOJkk5mTHkOlN5LhUjUokSXyU4AmPCSUiBMrQbjntjo85io7EniOxpXfGgB4QARsOajCo4HiQGYlU2ulJ6ThnIBCcKGP7vWbevnNfZ59nYbeRs8qSv5YNM1lB1WwSuI52eJzMnWNS9wEETZTzsK7px9jG3kKfV7Fciqlg3EwcH3Ir4TbMOEUrcwm1EqEfjR1MLmYDjg97GIl6MrwHfvMIKmHRNXaV7MTvGRYnIUHfYvZ22x25TvbRN1rKnVansK5Pl7k3eDq8vHooZUk9yvs1Zivl9JWZyzslq5UTSDEgRwZJ1thobYznoNPGT5He3Q1rTiFBWCv8aVqrA0xfsrqp2j7xcQNrOUgv9sRbhenmArwzA3MKxZLrBbAZ3srCklQlpEPp7h3G9qLGpNmmQItaZjOSxfgFbvnY3VJ7jSGKWryaThBjEblhYhZOQ6GoQXxH3N3C6qrM80fOXL3yzIUtJCFZlpavf8PWcgKrKrhzjGAxMogAS9NRJAXpOrekkcQPtKzSz1ISZsnWUpyQrhUngKEwKfuwluocJCrfCzZ166VZty7N50LjhTmVfjkXw8PTEPN7y4vtLCrG9LsOcLBjXsnNBr4Y5zVFMqM3ivPPQl0jx3czyVSUyO6vHHl4ruS2R0Wrl12oMHB6aNkXEvTsS35qyq47GLVVY7E2HOKuD8JIk9922AOB3jS453q0vvnELp81fCYOlFTo5z9mwKTa6nJnJWn20IFLx8F74n8VKWHWyiUcQ1n4bzRUwwogaTzfMl9t7zQeOJv74qxePv3C4uACA2jGESwQ2i9qNgpnUgm96AI6LRwjPYLHaBbZaUV76E4PaTtvFANNUxLiVcI67qG72oniQhoNCPVKEDsqRqkXUjWAtVUOwhglNuwa94KMvkM8mmmumyWALuGtS7mMeCFXiZXLW31eg35vKnW2QNuSqmpRliAaZrnTkNRJNJVTDWupFwXmrk6Hr9Z2vyi14iwskl85ub3yQWWnrsjKWDTabkJEpzeF5YAs1ZMycN9szC3vzNXG1CYvwhZAekaMvZ51P0pX35YHyhYgNL8slw5LxT3SwlCKJbETKGLZoGuWtWN1OsJgJuot7GlhmUuXgIhce3Pv2UzUASqM8BNuQl3B98eB59F0ZK40bLyQ95fK60uszohU2T0QuRYD0ubtMxefhOctjMfckEGOqmUqUoQ7pBmONgaG2Eam5fURaFI1EjHB214hnTgpJt3s8sxto7ZMEaLRHkoNjjl3p4m1Q8WpksktwMq8tFcuBSrOczwJ9pJw7VEQyLfFYzSN6lW4fS8wjXjRTXLWmoAiPp6Nszr6zBCkn0zx0XFV6sA7sNOhTXcwt9XVGMiYAZKeOrbAYETVjCzgyw8GK6Pvo4LbpuySqSDykiUkFl6EUZ50ZNS8725ufyT2CapfH1TWQE5x1vK7k9QgZSc8Cj7jsGxeMFz9igDYuWQj7gU1lfpBriWAmUEZhJDkj7hVHqJtIT3tAiZoaG1KACHFV95X7ODKMHFana8OrMgA61B8ILF2PK8FcGYkr31T2qgo7lSpWqgBEwMUNz5zrHSZMlba2QPO4rtJ9DhF7f74N3ncC0RDSBqGk37FEVscrbsDoqa3ZnaJqRsfB3ZzjtXgVCByhyfM6rEWTohDCoqAce7Bfoel2upinC7IQyCphbz7e1gTRMnaBmYssGJZgsshJVPYXYxspnWiCpm9ArGOje5DhYyZQWXZ'  # NOQA


@when('I go to the secure-message page')
def step_impl_go_to_secure_message_create_page(context):
    context.browser.visit('/secure-message/messages/')


@when('I click create message')
def step_impl_click_create_message(context):
    context.browser.find_by_link_text('Create a message').click()


@then('The create message page will open')
def step_impl_open_create_message_page(context):
    assert is_element_present_by_id(context, 'send-message')


@when('I am on the create message page')
def step_impl_visit_create_message_page(context):
    context.browser.visit('/secure-message/create-message/')


@when('I have a message to send')
def step_impl_add_text_to_subject_and_body(context):
    context.browser.find_by_id('secure-message-subject').send_keys('Test Subject')
    context.browser.find_by_id('secure-message-body').send_keys('Test Body')


@when('I have a message with non alpha characters')
def step_impl_add_non_alpha_text_to_subject_and_body(context):
    context.browser.find_by_id('secure-message-subject').send_keys('[]!@£$%^&*()')
    context.browser.find_by_id('secure-message-body').send_keys('"?><:|}{+_±')


@when('I have a message with empty fields')
def step_impl_empty_subject_and_body(context):
    context.browser.find_by_id('secure-message-subject').send_keys('')
    context.browser.find_by_id('secure-message-body').send_keys('')


@when('I have a message with subject too long')
def step_impl_add_text_to_subject_too_long(context):
    context.browser.find_by_id('secure-message-subject').send_keys(maxtext100)
    context.browser.find_by_id('secure-message-body').send_keys('Test')


# The subject textarea in frontstage has an auto limit of 100 characters
@when('I click send with subject too long')
def step_impl_subject_too_long_send(context):
    length = context.browser.find_by_id('subject').length()
    assert length < 101
    context.browser.find_by_id('send-message').click()


@when('I have a message with body too long')
def step_impl_add_text_to_body_too_long(context):
    context.browser.find_by_id('secure-message-subject').send_keys('Test')
    context.browser.find_by_id('secure-message-body').send_keys(maxtext10000)


@when('I send a message')
def step_impl_send_a_message(context):
    context.browser.find_by_id('send-message').click()


@then('The confirmation sent page opens')
def step_impl_open_confirmation_page(context):
    assert is_element_present_by_id(context, 'message-sent')


@given('I have received a message from BRES')
def step_impl_received_message_from_bres(context):
    url = 'http://localhost:5050/message/send'
    # This authorization needs to be valid for the user or the test will not work
    headers['Authorization'] = 'eyJ0eXAiOiJqd3QiLCJhbGciOiJIUzI1NiJ9.eyJwYXJ0eV9pZCI6IkJSRVMiLCJy' \
                               'b2xlIjoiaW50ZXJuYWwifQ.y_B0MsBwFbwUBadYvtn5ZppWRrw4Z-3JW9_ZXDprLug'
    headers['Content-Type'] = 'application/json'
    message = {
        "msg_to": ["0ab69a7c-21ce-40e5-a451-49eeb84ceeda"],
        "msg_from": "BRES",
        "subject": "Test internal message",
        "body": "Test internal message",
        "thread_id": "",
        "ru_id": "f1a5e99c-8edf-489a-9c72-6cabe6c387fc",
        "collection_case": "ACollectionCase",
        "survey": "BRES"
    }
    requests.post(url, data=json.dumps(message), headers=headers)


@when('I go to the inbox tab')
def step_impl_go_to_inbox_tab(context):
    context.browser.visit('/secure-message/messages/INBOX')


@when('I open the internal message')
def step_impl_open_internal_message(context):
    context.browser.find_by_link_text('Test internal message').click()


@then('I should see a reply message')
def step_impl_see_message_from_bres(context):
    assert is_element_present_by_id(context, 'secure-message-subject')  # TODO find some values inside textfield
    assert is_element_present_by_id(context, 'secure-message-body')


@when('I reply to a BRES message')
def step_impl_reply_to_bres_message(context):
    context.browser.find_by_id('secure-message-body').send_keys('I am replying to BRES')
    context.browser.find_by_id('submit-btn').click()


@then('The draft saved text should appear')
def step_impl_draft_saved_text_appears(context):
    assert is_element_present_by_id(context, 'message-sent')


@then('I should receive a subject and body error')
def step_impl_subject_and_body_error(context):
    context.browser.find_by_link_text('Please enter a subject')
    context.browser.find_by_link_text('Please enter a message')


@then('I should receive a body too long error')
def step_impl_subject_and_body_error(context):
    context.browser.find_by_link_text('Body field length must not be greater than 10000')
