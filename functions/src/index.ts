// ////////////////////////////////////////////////////////////////////////////
// Garage Manage Cloud Functions定義
// ////////////////////////////////////////////////////////////////////////////

import * as functions from "firebase-functions";
import * as admin from "firebase-admin";

admin.initializeApp(functions.config().firebase);
const store = admin.firestore();

// ////////////////////////////////////////////////////////////////////////////
// Picoの操作
// ////////////////////////////////////////////////////////////////////////////
export const pico =
functions.region("asia-northeast1").https.onCall(async (data, context) => {
  functions.logger.info("start pico");
  if (!context.auth) {
    throw new functions.https.HttpsError("unauthenticated", "auth error");
  }
  functions.logger.info("update pico id : " + data.picoId);
  const docRef = store.collection("picos").doc(data.picoId);

  const doc = await docRef.get();
  let bottom = Number(doc.get("bottom"));
  bottom = bottom < data.shutter ? data.shutter : bottom;
  let top = Number(doc.get("top"));
  top = top > data.shutter ? data.shutter : top;
  const present = (data.shutter - top) / (bottom - top) * 100;
  const light = data.light;
  const fan = data.fan;

  docRef.update({
    "top": top,
    "bottom": bottom,
    "present": present,
    "light": light,
    "fan": fan,
    "ip": context.rawRequest.ip,
  });
  return {response: "OK"};
});

export const shutter =
functions.region("asia-northeast1").https.onCall(async (data, context) => {
  functions.logger.info("start manage");
  if (!context.auth) {
    throw new functions.https.HttpsError("unauthenticated", "auth error");
  }

});
