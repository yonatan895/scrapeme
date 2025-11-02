{{- define "scrapeme-app.name" -}}
{{ include "common.names.name" . | default .Chart.Name }}
{{- end }}
{{- define "scrapeme-app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{ .Values.fullnameOverride }}
{{- else }}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end }}
{{- define "scrapeme-app.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
{{- define "scrapeme-app.selectorLabels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
{{- define "scrapeme-app.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{ default (include "scrapeme-app.fullname" .) .Values.serviceAccount.name }}
{{- else -}}
{{ default "default" .Values.serviceAccount.name }}
{{- end -}}
{{- end }}
