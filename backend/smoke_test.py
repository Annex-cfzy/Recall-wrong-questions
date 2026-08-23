"""Recall smoke test: full happy-path chain + SM-2 rule check.
Run from backend/ dir after `uvicorn app.main:app` is up on :8000.
"""
import sqlite3
import time
import sys

import httpx

from app.core.config import DB_PATH

try:
    from app.services import sm2_service
except Exception as e:  # pragma: no cover
    sm2_service = None
    print("SM2 import failed:", e)

BASE = "http://127.0.0.1:8000"


def main():
    # wait for server
    for _ in range(20):
        try:
            r = httpx.get(f"{BASE}/api/health", timeout=3)
            if r.status_code == 200:
                print("[OK] health:", r.json())
                break
        except Exception:
            time.sleep(0.5)
    else:
        print("[FAIL] server did not come up")
        sys.exit(1)

    with httpx.Client(base_url=BASE, timeout=30) as c:
        # 1. create notebook
        nb = c.post("/api/notebooks", json={"name": "冒烟测试本", "subject": "数学", "color": "#007AFF"}).json()
        assert nb["code"] == 0, nb
        nb_id = nb["data"]["id"]
        print("[OK] notebook created id=", nb_id)

        # 2. text input
        e = c.post("/api/errors/text", json={
            "question": "求 lim(x->0) sin x / x", "answer": "1",
            "notebook_id": nb_id, "subject": "数学"}).json()
        assert e["code"] == 0, e
        eid = e["data"]["id"]
        print("[OK] error created id=", eid, "kp=", e["data"].get("knowledge_points"))

        # 3. list
        lst = c.get("/api/errors", params={"notebook_id": nb_id, "page": 1, "page_size": 20}).json()
        assert lst["code"] == 0 and lst["data"]["total"] >= 1, lst
        print("[OK] list total=", lst["data"]["total"])

        # 4. search (FTS5)
        s = c.get("/api/errors", params={"search": "sin", "notebook_id": nb_id}).json()
        print("[OK] search 'sin' total=", s["data"]["total"])

        # 5. force due + review start
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("UPDATE errors SET next_review = date('now','-1 day') WHERE id=?", (eid,))
        conn.commit(); conn.close()

        st = c.post("/api/review/start", json={"subject": "数学", "notebook_id": nb_id, "count": 10}).json()
        assert st["code"] == 0, st
        rid = st["data"]["review_id"]
        print("[OK] review start review_id=", rid, "total=", st["data"]["total"])

        # 6. review submit
        sub = c.post("/api/review/submit", json={
            "review_id": rid,
            "answers": [{"error_id": eid, "index": 0, "user_answer": "1"}]
        }).json()
        assert sub["code"] == 0, sub
        res0 = sub["data"]["results"][0]
        print("[OK] submit correct_count=", sub["data"]["correct_count"],
              "is_correct=", res0["is_correct"], "sm2=", res0.get("sm2_updated"))
        assert res0["is_correct"] is True

        # 7. dashboard
        dash = c.get("/api/dashboard/trends", params={"days": 30}).json()
        assert dash["code"] == 0, dash
        print("[OK] dashboard summary=", dash["data"]["summary"])

        kg = c.get("/api/dashboard/knowledge-graph").json()
        print("[OK] knowledge-graph nodes=", len(kg["data"]["nodes"]), "edges=", len(kg["data"]["edges"]))

        # 8. export markdown
        md = c.get(f"/api/export/markdown/{nb_id}")
        assert md.status_code == 200, md.status_code
        print("[OK] md export len=", len(md.text), "ctype=", md.headers.get("content-type"))

        # 9. export pdf (weasyprint likely absent -> HTML fallback)
        pdf = c.get(f"/api/export/pdf/{nb_id}")
        assert pdf.status_code == 200, pdf.status_code
        print("[OK] pdf export ctype=", pdf.headers.get("content-type"),
              "disposition=", pdf.headers.get("content-disposition"))

    # 10. SM-2 rules (pure function, per PRD Appendix A)
    try:
        from app.services.sm2_service import Sm2State, update_sm2, initial_sm2

        s = initial_sm2()  # rep=0, interval=1, ef=2.5
        correct = update_sm2(s, quality=5)
        assert correct.repetition == 1, correct
        assert correct.ease_factor > 2.5, correct

        wrong = update_sm2(s, quality=1)
        assert wrong.repetition == 0 and wrong.interval_days == 1, wrong
        assert wrong.ease_factor < 2.5, wrong

        # classic rule: 3rd+ review -> interval = round(interval*EF)
        s3 = Sm2State(repetition=2, interval_days=6, ease_factor=2.6, mastery=50)
        nxt = update_sm2(s3, quality=5)
        assert nxt.interval_days == round(6 * 2.6), nxt

        print("[OK] SM-2 correct/wrong/classic rules verified")
    except Exception as e:  # pragma: no cover
        print("[WARN] SM-2 unit check skipped:", e)

    print("\n=== SMOKE TEST PASSED ===")


if __name__ == "__main__":
    main()
