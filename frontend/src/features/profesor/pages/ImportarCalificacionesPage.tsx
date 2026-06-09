import { useParams, useNavigate } from 'react-router-dom'
import { ImportStepper } from '../components/ImportStepper'
import { DropzoneUpload } from '../components/DropzoneUpload'
import { TablaActividadesPreview } from '../components/TablaActividadesPreview'
import { useImportarCalificaciones } from '../hooks/useImportarCalificaciones'
import { Button } from '@/shared/components/ui/Button'

/**
 * Flujo de importación de calificaciones: 3 pasos.
 * Step 1: upload (DropzoneUpload)
 * Step 2: preview actividades (TablaActividadesPreview + selección)
 * Step 3: confirmar → redirect a ComisionPage
 */
export function ImportarCalificacionesPage() {
  const { comisionId } = useParams<{ comisionId: string }>()
  const navigate = useNavigate()

  const {
    step,
    actividadesDetectadas,
    seleccionadas,
    error,
    isUploading,
    isImporting,
    uploadFile,
    confirmar,
    toggleActividad,
    goBack,
  } = useImportarCalificaciones(comisionId ?? '')

  const handleConfirmar = async () => {
    confirmar()
    // Navigate on success is handled by checking step === 'confirmar' after mutation
  }

  // Navigate to comision page after successful import
  if (step === 'confirmar' && !isImporting) {
    navigate(`/profesor/comisiones/${comisionId}`, { replace: true })
    return null
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="text-sm text-slate-500 hover:text-slate-700"
        >
          ← Volver
        </button>
        <h1 className="text-2xl font-semibold text-slate-900">Importar Calificaciones</h1>
      </div>

      <ImportStepper currentStep={step} />

      {/* Step 1: Upload */}
      {step === 'upload' && (
        <div className="rounded-xl border border-slate-200 bg-white p-8">
          <h2 className="mb-4 text-lg font-medium text-slate-900">
            Subir archivo de calificaciones
          </h2>
          <p className="mb-6 text-sm text-slate-500">
            Exportá el archivo desde Moodle en formato CSV o Excel y subilo acá.
          </p>
          <DropzoneUpload onFile={uploadFile} isLoading={isUploading} />
          {error && (
            <p role="alert" className="mt-4 text-sm text-red-600">
              {error}
            </p>
          )}
        </div>
      )}

      {/* Step 2: Preview actividades */}
      {step === 'preview' && (
        <div className="rounded-xl border border-slate-200 bg-white p-8 space-y-4">
          <h2 className="text-lg font-medium text-slate-900">
            Seleccionar actividades a importar
          </h2>
          <p className="text-sm text-slate-500">
            Se detectaron {actividadesDetectadas.length} actividades. Seleccioná las que querés importar.
          </p>

          <TablaActividadesPreview
            actividades={actividadesDetectadas}
            seleccionadas={seleccionadas}
            onToggle={toggleActividad}
          />

          {error && (
            <p role="alert" className="text-sm text-red-600">
              {error}
            </p>
          )}

          <div className="flex justify-between pt-4">
            <Button variant="secondary" onClick={goBack}>
              Volver
            </Button>
            <Button
              onClick={handleConfirmar}
              isLoading={isImporting}
              disabled={seleccionadas.length === 0}
            >
              Confirmar importación ({seleccionadas.length} actividades)
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
