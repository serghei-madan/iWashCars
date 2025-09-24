'use client'

import { useParams } from 'next/navigation'
import Image from 'next/image'
import Link from 'next/link'
import { ChevronLeft, Check } from 'lucide-react'

const services = {
  'exterior-wash': {
    title: 'Exterior Wash',
    description: 'Professional hand wash that removes dirt, grime, and road salt while protecting your paint',
    price: 'Starting at $25',
    duration: '30-45 minutes',
    images: [
      '/service-exterior-1.jpg',
      '/service-exterior-2.jpg',
    ],
    features: [
      'Hand wash with premium soap',
      'Wheel and tire cleaning',
      'Window cleaning inside and out',
      'Door jamb cleaning',
      'Tire dressing application',
      'Final inspection and touch-ups'
    ],
    process: [
      'Pre-rinse to remove loose dirt',
      'Application of premium car shampoo',
      'Gentle hand wash using microfiber mitts',
      'Thorough rinse',
      'Chamois dry to prevent water spots',
      'Detail finishing touches'
    ]
  },
  'interior-detailing': {
    title: 'Interior Detailing',
    description: 'Deep cleaning and conditioning of all interior surfaces for a like-new cabin experience',
    price: 'Starting at $75',
    duration: '1.5-2 hours',
    images: [
      '/service-interior-1.jpg',
      '/service-interior-2.jpg',
    ],
    features: [
      'Complete vacuum of seats, carpets, and trunk',
      'Steam cleaning of fabric surfaces',
      'Leather cleaning and conditioning',
      'Dashboard and console detailing',
      'Air vent cleaning',
      'Odor elimination treatment'
    ],
    process: [
      'Remove floor mats and vacuum thoroughly',
      'Clean and condition all surfaces',
      'Steam clean carpets and upholstery',
      'Clean all glass surfaces',
      'Apply protectant to dashboard and trim',
      'Final vacuum and inspection'
    ]
  },
  'paint-protection': {
    title: 'Paint Protection',
    description: 'Advanced ceramic coating and paint protection film to keep your car looking new for years',
    price: 'Starting at $300',
    duration: '4-6 hours',
    images: [
      '/service-paint-1.jpg',
      '/service-paint-2.jpg',
    ],
    features: [
      'Paint decontamination',
      'Clay bar treatment',
      'Multi-stage paint correction',
      'Ceramic coating application',
      'Hydrophobic protection',
      '2-5 year warranty options'
    ],
    process: [
      'Thorough wash and decontamination',
      'Clay bar treatment to remove embedded contaminants',
      'Paint correction to remove swirls and scratches',
      'Surface preparation with IPA wipe',
      'Ceramic coating application',
      'Curing and final inspection'
    ]
  },
  'full-detailing': {
    title: 'Full Detailing',
    description: 'Complete interior and exterior restoration bringing your vehicle back to showroom condition',
    price: 'Starting at $200',
    duration: '3-4 hours',
    images: [
      '/service-full-1.jpg',
      '/service-full-2.jpg',
    ],
    features: [
      'Everything from Exterior Wash',
      'Everything from Interior Detailing',
      'Engine bay cleaning',
      'Paint enhancement polish',
      'Headlight restoration',
      'Chrome and trim polishing'
    ],
    process: [
      'Complete exterior wash and decontamination',
      'Full interior deep clean',
      'Paint enhancement and protection',
      'Engine bay detailing',
      'All glass cleaned and treated',
      'Final quality inspection'
    ]
  },
  'mobile-service': {
    title: 'Mobile Service',
    description: 'We come to you! Professional detailing at your home or office for ultimate convenience',
    price: 'Starting at $50',
    duration: 'Varies by service',
    images: [
      '/service-mobile-1.jpg',
      '/service-mobile-2.jpg',
    ],
    features: [
      'Service at your location',
      'Fully equipped mobile unit',
      'Water and power self-contained',
      'All standard services available',
      'Flexible scheduling',
      'No travel fees within service area'
    ],
    process: [
      'Schedule appointment at your convenience',
      'Our team arrives with all equipment',
      'Set up protective coverings if needed',
      'Perform requested services',
      'Clean up work area',
      'Quality inspection with customer'
    ]
  },
  'specialty-services': {
    title: 'Specialty Services',
    description: 'Unique solutions for specific needs including pet hair removal, smoke odor treatment, and more',
    price: 'Quote on request',
    duration: 'Varies by service',
    images: [
      '/service-specialty-1.jpg',
      '/service-specialty-2.jpg',
    ],
    features: [
      'Pet hair removal',
      'Smoke odor elimination',
      'Headlight restoration',
      'Scratch and swirl removal',
      'Water spot removal',
      'Mold remediation'
    ],
    process: [
      'Initial assessment of specific needs',
      'Custom treatment plan development',
      'Specialized product application',
      'Multiple treatment stages as needed',
      'Testing and verification',
      'Follow-up care instructions'
    ]
  }
}

export default function ServiceDetailPage() {
  const params = useParams()
  const serviceId = params.id as string
  const service = services[serviceId as keyof typeof services]

  if (!service) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Service Not Found</h1>
          <Link href="/services" className="text-blue-600 hover:underline">
            Back to Services
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-blue-600 text-white py-20">
        <div className="container mx-auto px-4">
          <Link 
            href="/services" 
            className="inline-flex items-center text-white/80 hover:text-white mb-4 transition-colors"
          >
            <ChevronLeft className="w-5 h-5 mr-1" />
            Back to Services
          </Link>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">{service.title}</h1>
          <p className="text-xl text-white/90 max-w-3xl">
            {service.description}
          </p>
          <div className="mt-6 flex flex-wrap gap-4">
            <div className="bg-white/10 rounded-lg px-4 py-2">
              <p className="text-sm text-white/70">Price</p>
              <p className="text-lg font-semibold">{service.price}</p>
            </div>
            <div className="bg-white/10 rounded-lg px-4 py-2">
              <p className="text-sm text-white/70">Duration</p>
              <p className="text-lg font-semibold">{service.duration}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-12">
        <div className="grid md:grid-cols-2 gap-12">
          <div>
            <h2 className="text-3xl font-bold mb-6">What's Included</h2>
            <ul className="space-y-3">
              {service.features.map((feature, index) => (
                <li key={index} className="flex items-start">
                  <Check className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">{feature}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="text-3xl font-bold mb-6">Our Process</h2>
            <ol className="space-y-4">
              {service.process.map((step, index) => (
                <li key={index} className="flex items-start">
                  <span className="bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center font-semibold mr-3 flex-shrink-0">
                    {index + 1}
                  </span>
                  <span className="text-gray-700 pt-1">{step}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>

        <div className="mt-16">
          <h2 className="text-3xl font-bold mb-8">Gallery</h2>
          <div className="grid md:grid-cols-2 gap-8">
            {service.images.map((image, index) => (
              <div key={index} className="bg-gray-200 rounded-lg overflow-hidden aspect-video relative">
                <div className="absolute inset-0 flex items-center justify-center text-gray-400">
                  <p>Image placeholder: {image}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-16 bg-blue-50 rounded-2xl p-8 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Book?</h2>
          <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
            Give your car the care it deserves. Book your {service.title.toLowerCase()} service today!
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/booking"
              className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Book Now
            </Link>
            <Link
              href="/contact"
              className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold border-2 border-blue-600 hover:bg-blue-50 transition-colors"
            >
              Contact Us
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}