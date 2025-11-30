"""
Reports Celery Tasks

Report generation tasks.
"""

from celery import shared_task
import pandas as pd
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.core.files import File

from .models import Report
from apps.forecasting.models import Forecast


@shared_task
def generate_report(report_id):
    """
    Generate report based on type and parameters
    
    This creates Excel/CSV/PDF reports with forecast data and analytics.
    """
    try:
        report = Report.objects.get(id=report_id)
        report.status = 'GENERATING'
        report.save()
        
        # Get report parameters
        params = report.parameters or {}
        
        if report.report_type == 'FORECAST':
            # Generate forecast report
            forecasts = Forecast.objects.all()
            
            if params.get('date_from'):
                forecasts = forecasts.filter(
                    forecast_date__gte=params['date_from']
                )
            
            if params.get('date_to'):
                forecasts = forecasts.filter(
                    forecast_date__lte=params['date_to']
                )
            
            # Convert to DataFrame
            data = []
            for fc in forecasts:
                data.append({
                    'Disease': fc.disease,
                    'Region': fc.region,
                    'Date': fc.forecast_date,
                    'Predicted Cases': fc.predicted_cases,
                    'Model': fc.model.name,
                })
            
            df = pd.DataFrame(data)
            
            # Save based on format
            media_root = Path(settings.MEDIA_ROOT)
            report_dir = media_root / 'reports'
            report_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if report.format == 'EXCEL':
                file_path = report_dir / f"{filename}.xlsx"
                df.to_excel(file_path, index=False)
            elif report.format == 'CSV':
                file_path = report_dir / f"{filename}.csv"
                df.to_csv(file_path, index=False)
            else:
                raise ValueError(f"Unsupported format: {report.format}")
            
            # Save file to model
            with open(file_path, 'rb') as f:
                report.file.save(file_path.name, File(f), save=False)
            
            report.status = 'COMPLETED'
            report.completed_at = datetime.now()
            report.save()
            
            return {'status': 'success', 'report_id': report_id}
        
        else:
            raise ValueError(f"Unsupported report type: {report.report_type}")
    
    except Exception as e:
        report = Report.objects.get(id=report_id)
        report.status = 'FAILED'
        report.save()
        
        return {'status': 'error', 'message': str(e)}
