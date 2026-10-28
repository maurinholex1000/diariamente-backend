import io
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.diary_entry import DiaryEntry
from app.models.user import User
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER


class ReportService:
    @staticmethod
    def generate_report(patient_id, start_date, end_date, db: Session) -> dict:
        entries = (
            db.query(DiaryEntry)
            .filter(
                DiaryEntry.user_id == patient_id,
                DiaryEntry.created_at >= start_date,
                DiaryEntry.created_at <= end_date,
            )
            .order_by(DiaryEntry.created_at.desc())
            .all()
        )

        patient = db.query(User).filter(User.id == patient_id).first()

        distortions = {}
        emotions = {}
        for e in entries:
            if e.detected_distortion and e.detected_distortion != "sin_distorsion":
                distortions[e.detected_distortion] = distortions.get(e.detected_distortion, 0) + 1
            if e.user_emotion:
                emotions[e.user_emotion] = emotions.get(e.user_emotion, 0) + 1

        return {
            "paciente": {
                "id": patient_id,
                "nombre": patient.username if patient else "No identificado",
            },
            "periodo": {
                "desde": start_date.strftime("%Y-%m-%d"),
                "hasta": end_date.strftime("%Y-%m-%d"),
            },
            "resumen": {
                "total_pensamientos": len(entries),
                "distorsiones_mas_frecuentes": [
                    {"distorsion": k, "cantidad": v}
                    for k, v in sorted(distortions.items(), key=lambda x: x[1], reverse=True)[:5]
                ],
                "emociones_mas_frecuentes": [
                    {"emocion": k, "cantidad": v}
                    for k, v in sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:5]
                ],
            },
            "pensamientos": [
                {
                    "fecha": e.created_at.strftime("%Y-%m-%d %H:%M"),
                    "situacion_activadora": e.antecedent,
                    "pensamiento_automatico": e.belief,
                    "emocion_detectada_ia": e.detected_emotion,
                    "distorsion_detectada_ia": e.detected_distortion,
                    "emocion_seleccionada_usuario": e.user_emotion,
                    "consecuencia": e.consequence,
                }
                for e in entries
            ],
        }

    @staticmethod
    def generate_pdf(report_data: dict) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            "CustomTitle", parent=styles["Heading1"], fontSize=24,
            textColor=colors.HexColor("#2D3748"), alignment=TA_CENTER, spaceAfter=30,
        )
        story.append(Paragraph("DIAriaMENTE - Reporte Clínico", title_style))
        story.append(Paragraph(f"Paciente: {report_data['paciente']['nombre']}", styles["Normal"]))
        story.append(Paragraph(
            f"Período: {report_data['periodo']['desde']} al {report_data['periodo']['hasta']}",
            styles["Normal"],
        ))
        story.append(Spacer(1, 20))

        story.append(Paragraph("Distorsiones Cognitivas Detectadas", styles["Heading2"]))
        dist_data = [["Distorsión", "Frecuencia"]]
        for d in report_data["resumen"]["distorsiones_mas_frecuentes"]:
            dist_data.append([d["distorsion"], str(d["cantidad"])])
        if len(dist_data) > 1:
            dist_table = Table(dist_data, colWidths=[3 * 120, 1 * 120])
            dist_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C9B1FF")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8F9FE")),
                ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
            ]))
            story.append(dist_table)

        story.append(Spacer(1, 20))
        story.append(Paragraph("Emociones Registradas", styles["Heading2"]))
        emo_data = [["Emoción", "Frecuencia"]]
        for e in report_data["resumen"]["emociones_mas_frecuentes"]:
            emo_data.append([e["emocion"], str(e["cantidad"])])
        if len(emo_data) > 1:
            emo_table = Table(emo_data, colWidths=[3 * 120, 1 * 120])
            emo_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFB3C6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8F9FE")),
                ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
            ]))
            story.append(emo_table)

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()